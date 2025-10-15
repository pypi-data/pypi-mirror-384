from typing import Dict

from deeploy.models import UpdateNonManagedDeploymentBase


class UpdateRegistrationDeployment(UpdateNonManagedDeploymentBase):
    """Class that contains the options for updating a Registration Deployment"""

    def to_request_body(self) -> Dict:
        request_body = {
            **super().to_request_body(),
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        return {k: v for k, v in request_body.items() if v is not None and v != {}}
