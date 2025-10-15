from enum import Enum


class InferenceEndpoint(Enum):
    """Class that contains the inference endpoint options"""

    PREDICT = "predict"
    EXPLAIN = "explain"
