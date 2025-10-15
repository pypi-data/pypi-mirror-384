from typing import Dict

from deeploy.enums import DeploymentType
from deeploy.models import CreateNonManagedDeploymentBase


class CreateRegistrationDeployment(CreateNonManagedDeploymentBase):
    """Class that contains the options for creating a registration deployment"""

    def to_request_body(self) -> Dict:
        request_body = {**super().to_request_body(deployment_type=DeploymentType.REGISTRATION)}
        filtered_request_body = {k: v for k, v in request_body.items() if v is not None and v != {}}
        return filtered_request_body
