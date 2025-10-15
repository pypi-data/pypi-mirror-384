from typing import Dict, Optional

from pydantic import BaseModel

from deeploy.enums import GuardrailType


class CreateGuardrail(BaseModel):
    """Class that contains the options for creating a guardrail"""

    name: str
    """str: a unique name for the guardrail"""
    
    apply_to_input: bool
    """boolean: whether to apply guardrail to input"""

    apply_to_output: bool
    """boolean: whether to apply guardrail to output"""

    regex: str
    """str: the regex pattern to match against input or output"""

    replacement: Optional[str] = "****"
    """str: the replacement string to use when the regex matches"""

    def to_request_body(self) -> Dict:
        return {
            "name": self.name,
            "applyToInput": self.apply_to_input,
            "applyToOutput": self.apply_to_output,
            "regex": self.regex,
            "replacement": self.replacement,
            "guardrailType": GuardrailType.REGEX.value,
        }
