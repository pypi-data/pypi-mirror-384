from enum import Enum


class ProblemType(Enum):
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLASSIFICATION_WITH_PROBABILITIES = "classificationWithProbabilities"
    TEXT_GENERATION = "textGeneration"
