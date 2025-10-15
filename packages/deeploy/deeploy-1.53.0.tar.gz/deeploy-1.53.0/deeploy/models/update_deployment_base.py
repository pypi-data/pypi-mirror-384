from typing import Dict, List, Optional

from pydantic import BaseModel

from deeploy.enums import DeploymentType, ExplainerType, ModelType, TransformerType
from deeploy.enums.explainer_type import ExplainerFrameworkVersion
from deeploy.enums.model_type import ModelFrameworkVersion


class UpdateDeploymentBase(BaseModel):
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
    model_type: Optional[ModelType] = None
    """int: enum value from ModelType class"""
    model_framework_version: Optional[ModelFrameworkVersion] = None
    """string: enum value from ModelFrameworkVersion class"""
    explainer_type: Optional[ExplainerType] = None
    """int, optional: enum value from ExplainerType class. Defaults to 0 (no explainer)"""
    explainer_framework_version: Optional[ExplainerFrameworkVersion] = None
    """string: enum value from ExplainerFrameworkVersion class"""
    transformer_type: Optional[TransformerType] = None
    """int, optional: enum value from TransformerType class. Defaults to 0 (no transformer)"""
    model_config = {
        "protected_namespaces": (),  # For pydantic version 2x need to disable namespace protection for property model_*
    }
    approver_user_ids: Optional[List[str]] = None
    """List, optional: list of user UUIDs that are requested to submit approval for this version"""
    message_to_approvers: Optional[str] = None
    """str, optional: a message to the requested approvers (only relevant if approver_user_ids is defined)"""
    guardrail_ids: Optional[List[str]] = None
    """List, optional: list of guardrail UUIDs that will be added to this version"""

    def to_request_body(self) -> Dict:
        return {
            "deploymentType": self.deployment_type.value if self.deployment_type else None,
            "repositoryId": self.repository_id,
            "branchName": self.branch_name,
            "commit": self.commit,
            "contractPath": self.contract_path,
            "modelType": self.model_type.value if self.model_type else None,
            "modelFrameworkVersion": self.model_framework_version.value
            if self.model_framework_version
            else None,
            "explainerType": self.explainer_type.value if self.explainer_type else None,
            "explainerFrameworkVersion": self.explainer_framework_version.value
            if self.explainer_framework_version
            else None,
            "transformerType": self.transformer_type.value if self.transformer_type else None,
            "approverUserIds": self.approver_user_ids,
            "messageToApprovers": self.message_to_approvers,
            "guardrailIds": self.guardrail_ids,
        }
