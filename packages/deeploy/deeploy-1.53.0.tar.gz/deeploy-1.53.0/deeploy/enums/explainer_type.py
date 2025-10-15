from enum import Enum


class ExplainerType(Enum):
    """Class that contains explainer types"""

    NO_EXPLAINER = 0
    ANCHOR_TABULAR = 1
    ANCHOR_IMAGES = 2
    ANCHOR_TEXT = 3
    SHAP_KERNEL = 4
    PDP_TABULAR = 5
    MACE_TABULAR = 6
    CUSTOM = 7
    INTEGRATED_EXPLAINER = 8
    SHAP_TREE = 9
    SALIENCY = 10
    ATTENTION = 11


class ExplainerFrameworkVersion(Enum):
    """Class that contains explainer framework versions"""

    ALIBI_CURRENT = "0.9.4"
    SHAP_CURRENT = "0.46.0"
    OMNIXAI_CURRENT = "1.3.1"
    SHAP_0_42 = "shapkernel_0_42"
