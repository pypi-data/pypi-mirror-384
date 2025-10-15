from typing import Dict

from pydantic import BaseModel

from deeploy.enums.inference_endpoint import InferenceEndpoint


class CreateJobSchedule(BaseModel):
    """Class that contains the options for creating a job schedule"""

    name: str
    """str: a unique name for the job schedule"""
    cron_expression: str
    """str: the cron expression to decide how often the job should be executed"""
    deployment_id: str
    """str: the uuid of the Deployment which the job schedule should target"""
    endpoint: InferenceEndpoint = InferenceEndpoint.PREDICT
    """str: which endpoint the scheduled jobs should call. Defaults to predict"""

    def to_request_body(self) -> Dict:
        return {
            "name": self.name,
            "cronExpression": self.cron_expression,
            "deploymentId": self.deployment_id,
            "endpoint": self.endpoint.value,
        }
