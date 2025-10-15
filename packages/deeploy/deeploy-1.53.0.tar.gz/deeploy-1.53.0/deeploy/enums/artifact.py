from enum import Enum


class Artifact(Enum):
    """Class that contains artifact types"""

    MODEL = "model"
    EXPLAINER = "explainer"
    TRANSFORMER = "transformer"
