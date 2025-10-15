from typing import Dict, List, Optional

from pydantic import BaseModel

from deeploy.enums import DeploymentType


class UpdateNonManagedDeploymentBase(BaseModel):
    """Class that contains the base options for updating a Deployment"""

    deployment_type: Optional[DeploymentType] = None
    """str: enum value from DeploymentType class"""
    repository_id: Optional[str] = None
    """str, optional: uuid of the Repository"""
    branch_name: Optional[str] = None
    """str, optional: the branch name of the Repository to deploy"""
    commit: Optional[str] = None
    """str, optional: the commit sha on the selected branch"""
    contract_path: Optional[str] = None
    """str, optional: relative repository subpath that contains the Deeploy contract to deploy from"""
    approver_user_ids: Optional[List[str]] = None
    """List, optional: list of user UUIDs that are requested to submit approval for this version"""
    message_to_approvers: Optional[str] = None
    """str, optional: a message to the requested approvers (only relevant if approver_user_ids is defined)"""

    def to_request_body(self) -> Dict:
        return {
            "deploymentType": self.deployment_type.value if self.deployment_type else None,
            "repositoryId": self.repository_id,
            "branchName": self.branch_name,
            "commit": self.commit,
            "contractPath": self.contract_path,
            "approverUserIds": self.approver_user_ids,
            "messageToApprovers": self.message_to_approvers,
        }
