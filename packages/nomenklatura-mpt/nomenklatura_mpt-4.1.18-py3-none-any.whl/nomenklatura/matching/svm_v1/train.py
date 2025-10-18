import logging
import numpy as np
import multiprocessing
from typing import Iterable, List, Tuple, Optional
from pprint import pprint
from numpy.typing import NDArray
from sklearn.pipeline import make_pipeline  # type: ignore
from sklearn.preprocessing import StandardScaler  # type: ignore
from sklearn.model_selection import train_test_split, GridSearchCV  # type: ignore
from sklearn.svm import SVC  # type: ignore
from sklearn import metrics # type: ignore
from concurrent.futures import ProcessPoolExecutor
from followthemoney.util import PathLike

from nomenklatura.judgement import Judgement
from nomenklatura.matching.pairs import read_pairs, JudgedPair
from .model import SVMV1

log = logging.getLogger(__name__)


def pair_convert(pair: JudgedPair) -> Tuple[List[float], int]:
    """Encode a pair of training data into features and target."""
    judgement = 1 if pair.judgement == Judgement.POSITIVE else 0
    features = SVMV1.encode_pair(pair.left, pair.right)
    return features, judgement


def pairs_to_arrays(
    pairs: Iterable[JudgedPair],
) -> Tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Parallelize feature computation for training data"""
    xrows = []
    yrows = []
    workers = multiprocessing.cpu_count()
    log.info("Using %d processes for feature computation...", workers)
    with ProcessPoolExecutor(max_workers=workers) as excecutor:
        results = excecutor.map(pair_convert, pairs)
        for idx, (x, y) in enumerate(results):
            if idx > 0 and idx % 10000 == 0:
                log.info("Computing features: %s....", idx)
            xrows.append(x)
            yrows.append(y)

    return np.array(xrows), np.array(yrows)


def train_svm_matcher(
    pairs_file: PathLike, 
    kernel: str = "rbf",
    optimize_hyperparameters: bool = True,
    probability: bool = True
) :
    """Train an SVM matching model."""
    pairs = []
    for pair in read_pairs(pairs_file):
        if pair.judgement == Judgement.UNSURE:
            pair.judgement = Judgement.NEGATIVE
        pairs.append(pair)
    
    positive = len([p for p in pairs if p.judgement == Judgement.POSITIVE])
    negative = len([p for p in pairs if p.judgement == Judgement.NEGATIVE])
    log.info("Total pairs loaded: %d (%d pos/%d neg)", len(pairs), positive, negative)
    
    X, y = pairs_to_arrays(pairs)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)
    
    log.info("Training SVM model with %s kernel...", kernel)
    
    # Create base SVM
    if optimize_hyperparameters:
        log.info("Optimizing hyperparameters with Grid Search...")
        
        # Define parameter grid
        if kernel == "rbf":
            param_grid = {
                'svc__C': [0.1, 1, 10, 100],
                'svc__gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1]
            }
        elif kernel == "linear":
            param_grid = {
                'svc__C': [0.1, 1, 10, 100]
            }
        elif kernel == "poly":
            param_grid = {
                'svc__C': [0.1, 1, 10, 100],
                'svc__degree': [2, 3, 4],
                'svc__gamma': ['scale', 'auto', 0.001, 0.01, 0.1]
            }
        else:
            param_grid = {'svc__C': [0.1, 1, 10, 100]}
        
        # Create pipeline
        base_svm = SVC(kernel=kernel, probability=probability, random_state=42)
        pipeline = make_pipeline(StandardScaler(), base_svm)
        
        # Grid search
        grid_search = GridSearchCV(
            pipeline, 
            param_grid, 
            cv=5, 
            scoring='roc_auc',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        pipeline = grid_search.best_estimator_
        
        log.info("Best parameters: %s", grid_search.best_params_)
        log.info("Best cross-validation score: %.4f", grid_search.best_score_)
        
    else:
        # Use default parameters
        svm = SVC(kernel=kernel, probability=probability, random_state=42)
        pipeline = make_pipeline(StandardScaler(), svm)
        pipeline.fit(X_train, y_train)
    
    # Get SVM object for coefficient extraction
    svm_model = pipeline.named_steps['svc']
    
    # Create feature coefficients (for linear kernel, use actual coefficients)
    coefficients = {}
    if kernel == "linear" and hasattr(svm_model, 'coef_'):
        # For linear SVM, we have actual feature coefficients
        coef_values = svm_model.coef_[0]
        for i, feature in enumerate(SVMV1.FEATURES):
            coefficients[feature.__name__] = float(coef_values[i])
    else:
        # For non-linear kernels, use feature importance approximation
        # This is a simplified approach - in practice, you might use SHAP or similar
        for feature in SVMV1.FEATURES:
            coefficients[feature.__name__] = 1.0  # Placeholder
    
    # Get support vector count
    support_vectors_count = len(svm_model.support_vectors_) if hasattr(svm_model, 'support_vectors_') else None
    
    # Save the model
    SVMV1.save(pipeline, coefficients, kernel, support_vectors_count)
    path = SVMV1.MODEL_PATH
    # Evaluation
    log.info("Evaluating SVM model...")
    
    # Predictions
    y_pred = pipeline.predict(X_test)
    
    if probability:
        y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
    else:
        # Use decision function and apply sigmoid
        decision_scores = pipeline.decision_function(X_test)
        y_pred_proba = 1.0 / (1.0 + np.exp(-decision_scores))
    
    # Print results
    print("\nSVM Results:")
    print(f"Kernel: {kernel}")
    print(f"Support vectors count: {support_vectors_count}")
    
    if kernel == "linear":
        print("Feature Coefficients:")
        pprint(coefficients)
    
    cnf_matrix = metrics.confusion_matrix(y_test, y_pred)
    print("Confusion matrix:\n", cnf_matrix)
    print("Accuracy:", metrics.accuracy_score(y_test, y_pred))
    print("Precision:", metrics.precision_score(y_test, y_pred))
    print("Recall:", metrics.recall_score(y_test, y_pred))
    print("F1-score:", metrics.f1_score(y_test, y_pred))
    
    auc = metrics.roc_auc_score(y_test, y_pred_proba)
    print("Area under curve:", auc)
    
    # Additional SVM-specific metrics
    if hasattr(svm_model, 'support_'):
        print(f"Number of support vectors: {len(svm_model.support_)}")
        print(f"Support vectors per class: {svm_model.n_support_}")
    return SVMV1.MODEL_PATH


def train_matcher(
    pairs_file: PathLike, 
    kernel: str = "rbf",
    optimize: bool = True
) -> None:
    """Wrapper function to maintain compatibility with existing training interface."""
    train_svm_matcher(pairs_file, kernel=kernel, optimize_hyperparameters=optimize)