import pickle
import numpy as np
from typing import List, Dict, Tuple, cast, Optional
from functools import lru_cache as cache
from sklearn.pipeline import Pipeline  # type: ignore
from sklearn.svm import SVC  # type: ignore
from sklearn.preprocessing import StandardScaler  # type: ignore
from followthemoney.proxy import E

from .names import first_name_match
from .names import family_name_match
from .names import name_levenshtein, name_match
from .names import name_token_overlap, name_numbers
from .names import name_length_similarity
from .misc import phone_match, email_match
from .misc import address_match, address_numbers
from .misc import identifier_match, birth_place
from .misc import org_identifier_match
from .misc import gender_mismatch
from .misc import country_mismatch
from .misc import schema_match, property_count_similarity
from nomenklatura.matching.compare.dates import dob_matches, dob_year_matches
from nomenklatura.matching.compare.dates import dob_year_disjoint
from nomenklatura.matching.types import (
    FeatureDocs,
    FeatureDoc,
    MatchingResult,
    ScoringConfig,
)
from nomenklatura.matching.types import CompareFunction, FtResult
from nomenklatura.matching.types import Encoded, ScoringAlgorithm
from nomenklatura.matching.util import make_github_url
from nomenklatura.util import DATA_PATH


class SVMV1(ScoringAlgorithm):
    """A Support Vector Machine-based matching algorithm with RBF kernel."""

    NAME = "svm-v1"
    MODEL_PATH = DATA_PATH.joinpath(f"{NAME}.pkl")
    FEATURES: List[CompareFunction] = [
        name_match,
        name_token_overlap,
        name_numbers,
        name_levenshtein,
        name_length_similarity,
        phone_match,
        email_match,
        identifier_match,
        dob_matches,
        dob_year_matches,
        FtResult.unwrap(dob_year_disjoint),
        first_name_match,
        family_name_match,
        birth_place,
        gender_mismatch,
        country_mismatch,
        org_identifier_match,
        address_match,
        address_numbers,
        schema_match,
        property_count_similarity,
    ]

    @classmethod
    def save(cls, 
             pipeline: Pipeline, 
             coefficients: Dict[str, float],
             kernel: str = "rbf",
             support_vectors_count: Optional[int] = None) -> None:
        """Store the SVM model after training."""
        mdl = pickle.dumps({
            "pipeline": pipeline,
            "coefficients": coefficients,
            "kernel": kernel,
            "support_vectors_count": support_vectors_count
        })
        with open(cls.MODEL_PATH, "wb") as fh:
            fh.write(mdl)
        cls.load.cache_clear()

    @classmethod
    @cache
    def load(cls) -> Tuple[Pipeline, Dict[str, float], str, Optional[int]]:
        """Load a pre-trained SVM model for ad-hoc use."""
        with open(cls.MODEL_PATH, "rb") as fh:
            model_data = pickle.loads(fh.read())
        
        pipeline = cast(Pipeline, model_data["pipeline"])
        coefficients = cast(Dict[str, float], model_data["coefficients"])
        kernel = cast(str, model_data.get("kernel", "rbf"))
        support_vectors_count = cast(Optional[int], model_data.get("support_vectors_count"))
        
        current = [f.__name__ for f in cls.FEATURES]
        if list(coefficients.keys()) != current:
            raise RuntimeError("Model was not trained on identical features!")
        
        return pipeline, coefficients, kernel, support_vectors_count

    @classmethod
    def get_feature_docs(cls) -> FeatureDocs:
        """Return an explanation of the features and their coefficients."""
        features: FeatureDocs = {}
        _, coefficients, _, _ = cls.load()
        for func in cls.FEATURES:
            name = func.__name__
            features[name] = FeatureDoc(
                description=func.__doc__,
                coefficient=float(coefficients.get(name, 0.0)),
                url=make_github_url(func),
            )
        return features

    @classmethod
    def compare(cls, query: E, result: E, config: ScoringConfig) -> MatchingResult:
        """Use an SVM model to compare two entities."""
        pipeline, coefficients, kernel, _ = cls.load()
        
        encoded = cls.encode_pair(query, result)
        npfeat = np.array([encoded])
        
        # Get probability predictions
        if hasattr(pipeline.named_steps['svc'], 'predict_proba'):
            pred_proba = pipeline.predict_proba(npfeat)
            score = float(pred_proba[0][1])  # Positive class probability
        else:
            # Fallback to decision function if predict_proba is not available
            decision = pipeline.decision_function(npfeat)
            # Convert decision function to probability-like score
            score = float(1.0 / (1.0 + np.exp(-decision[0])))  # Sigmoid transformation
        
        # Create explanations
        explanations: Dict[str, FtResult] = {}
        for feature, coeff in zip(cls.FEATURES, encoded):
            name = feature.__name__
            explanations[name] = FtResult(score=float(coeff), detail=None)
        
        # Add model-specific information
        explanations["svm_kernel"] = FtResult(score=0.0, detail=kernel)
        
        return MatchingResult.make(score=score, explanations=explanations)

    @classmethod
    def encode_pair(cls, left: E, right: E) -> Encoded:
        """Encode the comparison between two entities as a set of feature values."""
        return [f(left, right) for f in cls.FEATURES]

    @classmethod
    def get_decision_function(cls, features: np.ndarray) -> np.ndarray:
        """Get the SVM decision function values."""
        pipeline, _, _, _ = cls.load()
        return pipeline.decision_function(features)

    @classmethod
    def get_support_vectors_info(cls) -> Dict[str, any]:
        """Get information about the support vectors."""
        pipeline, _, kernel, sv_count = cls.load()
        svm = pipeline.named_steps['svc']
        
        info = {
            "kernel": kernel,
            "support_vectors_count": sv_count or len(svm.support_vectors_) if hasattr(svm, 'support_vectors_') else None,
            "n_support": svm.n_support_.tolist() if hasattr(svm, 'n_support_') else None,
            "gamma": svm.gamma if hasattr(svm, 'gamma') else None,
            "C": svm.C if hasattr(svm, 'C') else None,
        }
        
        return info