from typing import Dict, Optional

from pydantic import BaseModel


class UpdateDeploymentDescription(BaseModel):
    """Class that contains the options for updating a model that doesn't require restarting pods"""

    name: Optional[str] = None
    """str: name of the Deployment"""
    description: Optional[str] = None
    """str, optional: the description of the Deployment"""
    use_case_id: Optional[str] = None
    """str, optional: the uuid of the use case the Deployment is associated with"""

    def to_request_body(self) -> Dict:
        request_body = {
            "name": self.name,
            "description": self.description,
            "useCaseId": self.use_case_id,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        return {k: v for k, v in request_body.items() if v is not None and v != {}}
