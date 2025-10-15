from typing import Dict, Optional

from pydantic import BaseModel


class CreateEvaluation(BaseModel):
    """Class that contains the options for creating an Evaluation"""

    agree: bool
    """bool: whether the evaluator agrees of disagrees with the correctness of the prediction"""
    desired_output: Optional[Dict] = None
    """dict, optional: the desired output of the model presented by the expert"""
    comment: Optional[str] = None
    """str, optional: an optional comment/explanation on the evaluation"""

    def to_request_body(self) -> Dict:
        return {
            "agree": self.agree,
            "desiredOutput": self.desired_output,
            "comment": self.comment,
        }
