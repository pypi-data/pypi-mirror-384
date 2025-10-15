from typing import Dict, List, Optional

from pydantic import BaseModel

from deeploy.enums import (
    DeploymentType,
    ExplainerFrameworkVersion,
    ExplainerType,
    ModelFrameworkVersion,
    ModelType,
    TransformerType,
)


class CreateDeploymentBase(BaseModel):
    """Class that contains the base options for creating a Deployment"""

    name: str
    """str: name of the Deployment"""
    description: Optional[str] = None
    """str, optional: the description of the Deployment"""
    repository_id: str
    """str: uuid of the Repository"""
    branch_name: str
    """str: the branch name of the Repository to deploy"""
    commit: Optional[str] = None
    """str, optional: the commit sha on the selected branch. If no commit is provided, the latest commit will be used"""
    contract_path: Optional[str] = None
    """str, optional: relative repository subpath that contains the Deeploy contract to deploy from"""
    use_case_id: Optional[str] = None
    """str, optional: the uuid of the use case the Deployment is associated with. If no use case is provided, a new use case will be created automatically"""
    model_type: ModelType
    """int: enum value from ModelType class"""
    model_framework_version: Optional[ModelFrameworkVersion] = None
    """string: enum value from ModelFrameworkVersion class"""
    explainer_type: Optional[ExplainerType] = ExplainerType.NO_EXPLAINER
    """int, optional: enum value from ExplainerType class. Defaults to 0 (no explainer)"""
    explainer_framework_version: Optional[ExplainerFrameworkVersion] = None
    """string: enum value from ExplainerFrameworkVersion class"""
    transformer_type: Optional[TransformerType] = TransformerType.NO_TRANSFORMER
    """int, optional: enum value from TransformerType class. Defaults to 0 (no transformer)"""
    model_config = {
        "protected_namespaces": (),  # For pydantic version 2x need to disable namespace protection for property model_*
    }
    approver_user_ids: Optional[List[str]] = None
    """List, optional: list of user UUIDs that are requested to submit approval for this version"""
    message_to_approvers: Optional[str] = None
    """str, optional: a message to the requested approvers (only relevant if approver_user_ids is defined)"""
    documentation_template_ids: Optional[List[str]] = None
    """List, optional: list of documentation template UUIDs that will be added to the deployment"""
    guardrail_ids: Optional[List[str]] = None
    """List, optional: list of guardrail UUIDs that will be added to the deployment"""

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
            "modelType": self.model_type.value,
            "modelFrameworkVersion": self.model_framework_version.value
            if self.model_framework_version
            else None,
            "explainerType": self.explainer_type.value,
            "explainerFrameworkVersion": self.explainer_framework_version.value
            if self.explainer_framework_version
            else None,
            "transformerType": self.transformer_type.value,
            "approverUserIds": self.approver_user_ids,
            "messageToApprovers": self.message_to_approvers,
            "documentationTemplateIds": self.documentation_template_ids,
            "guardrailIds": self.guardrail_ids,
        }
