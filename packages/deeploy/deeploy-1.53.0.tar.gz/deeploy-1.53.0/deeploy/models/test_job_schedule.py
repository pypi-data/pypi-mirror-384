from typing import Dict

from pydantic import BaseModel

from deeploy.enums.inference_endpoint import InferenceEndpoint


class TestJobSchedule(BaseModel):
    """Class that contains the options for testing a job schedule"""

    deployment_id: str
    """str: the uuid of the Deployment which the test job schedule should target"""
    endpoint: InferenceEndpoint = InferenceEndpoint.PREDICT
    """str: which endpoint the test job should call. Defaults to predict"""

    def to_request_body(self) -> Dict:
        return {
            "deploymentId": self.deployment_id,
            "endpoint": self.endpoint.value,
        }
