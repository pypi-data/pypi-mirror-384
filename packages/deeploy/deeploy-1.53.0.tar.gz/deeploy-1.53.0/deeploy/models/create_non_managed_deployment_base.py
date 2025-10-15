from typing import Dict, List, Optional

from pydantic import BaseModel

from deeploy.enums import DeploymentType


class CreateNonManagedDeploymentBase(BaseModel):
    """Class that contains the base options for creating a Deployment"""

    name: str
    """str: name of the Deployment"""
    description: Optional[str] = None
    """str, optional: the description of the Deployment"""
    repository_id: Optional[str] = None
    """str, optional: uuid of the Repository"""
    branch_name: Optional[str] = None
    """str, optional: the branch name of the Repository to deploy"""
    commit: Optional[str] = None
    """str, optional: the commit sha on the selected branch. If no commit is provided, the latest commit will be used"""
    contract_path: Optional[str] = None
    """str, optional: relative repository subpath that contains the Deeploy contract to deploy from"""
    use_case_id: Optional[str] = None
    """str, optional: the uuid of the use case the Deployment is associated with. If no use case is provided, a new use case will be created automatically"""
    approver_user_ids: Optional[List[str]] = None
    """List, optional: list of user UUIDs that are requested to submit approval for this version"""
    message_to_approvers: Optional[str] = None
    """str, optional: a message to the requested approvers (only relevant if approver_user_ids is defined)"""
    documentation_template_ids: Optional[List[str]] = None
    """List, optional: list of documentation template UUIDs that will be added to the deployment"""

    def to_request_body(self, deployment_type: DeploymentType) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "useCaseId": self.use_case_id,
            "deploymentType": deployment_type.value,
            "repositoryId": self.repository_id,
            "branchName": self.branch_name,
            "commit": self.commit,
            "contractPath": self.contract_path,
            "approverUserIds": self.approver_user_ids,
            "messageToApprovers": self.message_to_approvers,
            "documentationTemplateIds": self.documentation_template_ids,
        }
