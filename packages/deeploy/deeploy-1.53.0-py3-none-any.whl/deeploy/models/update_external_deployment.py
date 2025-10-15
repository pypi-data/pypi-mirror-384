from typing import Dict, List, Optional

from deeploy.enums.external_url_authentication_method import ExternalUrlAuthenticationMethod
from deeploy.models import UpdateNonManagedDeploymentBase


class UpdateExternalDeployment(UpdateNonManagedDeploymentBase):
    """Class that contains the options for updating a External Deployment"""

    url: Optional[str] = None
    """str, optional: url endpoint of external deployment"""
    authentication: Optional[ExternalUrlAuthenticationMethod] = None
    """str, optional: enum value from ExternalUrlAuthenticationMethod class."""
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
    """List, optional: list of guardrail UUIDs that will be added to this version"""

    def to_request_body(self) -> Dict:
        request_body = {
            **super().to_request_body(),
            "url": self.url,
            "tokenURL": self.token_url,
            "username": self.username,
            "password": self.password,
            "authentication": self.authentication.value,
            "guardrailIds": self.guardrail_ids,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        return {k: v for k, v in request_body.items() if v is not None and v != {}}
