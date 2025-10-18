from typing import List, Type, Optional
from nomenklatura.matching.regression_v1.model import RegressionV1
from nomenklatura.matching.svm_v1.model import SVMV1
from nomenklatura.matching.regression_v1.train import train_matcher as train_v1_matcher
from nomenklatura.matching.svm_v1.train import train_matcher as train_svm_matcher
from nomenklatura.matching.name_based import NameMatcher, NameQualifiedMatcher
from nomenklatura.matching.erun.model import EntityResolveRegression
from nomenklatura.matching.erun.train import train_matcher as train_erun_matcher
from nomenklatura.matching.logic_v1.model import LogicV1
from nomenklatura.matching.logic_v2.model import LogicV2
from nomenklatura.matching.logic_v3.model import LogicV3
from nomenklatura.matching.logic_v4.model import LogicV4
from nomenklatura.matching.custom_v1.model import CustomV1
from nomenklatura.matching.types import ScoringAlgorithm, ScoringConfig

ALGORITHMS: List[Type[ScoringAlgorithm]] = [
    LogicV1,
    LogicV2,
    LogicV3,
    LogicV4,
    CustomV1,
    NameMatcher,
    NameQualifiedMatcher,
    RegressionV1,
    EntityResolveRegression,
    SVMV1
]

DefaultAlgorithm = RegressionV1


def get_algorithm(name: str) -> Optional[Type[ScoringAlgorithm]]:
    """Return the scoring algorithm class with the given name."""
    for algorithm in ALGORITHMS:
        if algorithm.NAME == name:
            return algorithm
    return None


__all__ = [
    "RegressionV1",
    "EntityResolveRegression",
    "train_v1_matcher",
    "train_svm_matcher",
    "train_erun_matcher",
    "DefaultAlgorithm",
    "ScoringAlgorithm",
    "NameMatcher",
    "NameQualifiedMatcher",
    "ScoringConfig",
    "LogicV1",
    "LogicV2",
    "LogicV3",
    "LogicV4",
    "CustomV1",
    "SVMV1",
]
