from enum import Enum


class ModelType(Enum):
    """Class that contains model types"""

    TENSORFLOW = 0
    PYTORCH = 1
    SKLEARN = 2
    XGBOOST = 3
    ONNX = 4
    TRITON = 5
    CUSTOM = 6
    LIGHTGBM = 7
    PMML = 8
    HUGGINGFACE = 9


class ModelFrameworkVersion(Enum):
    """Class that contains model framework versions"""

    XGBOOST_CURRENT = None
    SKLEARN_CURRENT = None
    LIGHTGBM_CURRENT = None
    XGBOOST_1_7_5 = "xgboost_1_7_5"
    SKLEARN_1_3_0 = "sklearn_1_3_0"
