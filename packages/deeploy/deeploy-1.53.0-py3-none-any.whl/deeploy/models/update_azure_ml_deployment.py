from typing import Dict, Optional

from deeploy.models import UpdateDeploymentBase


class UpdateAzureMLDeployment(UpdateDeploymentBase):
    """Class that contains the options for updating an Azure Machine Learning Deployment"""

    model_instance_type: Optional[str] = None
    """str, optional: the preferred instance type for the model"""
    model_instance_count: Optional[int] = None
    """int, optional: the amount of compute instances used for your model deployment"""
    explainer_instance_type: Optional[str] = None
    """str, optional: The preferred instance type for the explainer"""
    explainer_instance_count: Optional[int] = None
    """int, optional: the amount of compute instances used for your explainer deployment"""
    model_config = {
        "protected_namespaces": (),  # For pydantic version 2x need to disable namespace protection for property model_*
    }

    def to_request_body(self) -> Dict:
        request_body = {
            **super().to_request_body(),
            "modelInstanceType": self.model_instance_type,
            "modelInstanceCount": self.model_instance_count,
            "explainerInstanceType": self.explainer_instance_type,
            "explainerInstanceCount": self.explainer_instance_count,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        return {k: v for k, v in request_body.items() if v is not None and v != {}}
