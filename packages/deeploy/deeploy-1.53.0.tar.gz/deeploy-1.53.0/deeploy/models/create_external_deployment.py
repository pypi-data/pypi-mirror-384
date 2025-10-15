from typing import Dict, List, Optional

from deeploy.enums import DeploymentType
from deeploy.enums.external_url_authentication_method import ExternalUrlAuthenticationMethod
from deeploy.models import CreateNonManagedDeploymentBase


class CreateExternalDeployment(CreateNonManagedDeploymentBase):
    """Class that contains the options for creating a external deployment"""

    url: str
    """str, optional: url endpoint of external deployment"""
    authentication: ExternalUrlAuthenticationMethod
    """str: enum value from ExternalUrlAuthenticationMethod class."""
    token_url: Optional[str] = None
    """str, optional: the token url used for retrieving the access token for oauth authentication"""
    username: Optional[str] = None
    """str, optional: 
    username for basic authentication, or 
    header for custom authentication, or
    client id for oauth authentication
    """
    password: Optional[str] = None
    """str, optional: 
    password for basic authentication, or 
    bearer token for bearer authentication, or
    header value for custom authentication, or
    client secret for oauth authentication
    """
    guardrail_ids: Optional[List[str]] = None
    """List, optional: list of guardrail UUIDs that will be added to the deployment"""

    def to_request_body(self) -> Dict:
        request_body = {
            **super().to_request_body(deployment_type=DeploymentType.EXTERNAL),
            "url": self.url,
            "tokenURL": self.token_url,
            "username": self.username,
            "password": self.password,
            "authentication": self.authentication.value,
            "guardrailIds": self.guardrail_ids,
        }
        filtered_request_body = {k: v for k, v in request_body.items() if v is not None and v != {}}
        return filtered_request_body
