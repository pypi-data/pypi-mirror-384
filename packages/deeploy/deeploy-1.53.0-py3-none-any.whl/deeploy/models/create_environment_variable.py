from typing import Dict

from pydantic import BaseModel


class CreateEnvironmentVariable(BaseModel):
    """Class that contains the options for creating an environment variable"""

    name: str
    """str: a unique name for the environment variable"""
    key: str
    """str: the key of the environment variable"""
    value: str
    """str: the value of the environment variable"""

    def to_request_body(self) -> Dict:
        return {
            "name": self.name,
            "key": self.key,
            "value": self.value,
        }
