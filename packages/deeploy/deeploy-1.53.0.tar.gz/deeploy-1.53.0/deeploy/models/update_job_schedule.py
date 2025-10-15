from typing import Dict, Optional

from pydantic import BaseModel

from deeploy.enums.inference_endpoint import InferenceEndpoint


class UpdateJobSchedule(BaseModel):
    """Class that contains the options for creating a job schedule"""

    name: Optional[str] = None
    """str, optional: a unique name for the job schedule"""
    cron_expression: Optional[str] = None
    """str, optional: the cron expression to decide how often the job should be executed"""
    deployment_id: Optional[str] = None
    """str, optional: the uuid of the Deployment which the job schedule should target"""
    endpoint: Optional[InferenceEndpoint] = None
    """str: which endpoint the scheduled jobs should call"""

    def to_request_body(self) -> Dict:
        request_body = {
            "name": self.name,
            "cronExpression": self.cron_expression,
            "deploymentId": self.deployment_id,
            "endpoint": self.endpoint.value if self.endpoint else None,
        }
        filtered_request_body = {k: v for k, v in request_body.items() if v is not None and v != {}}
        return filtered_request_body
