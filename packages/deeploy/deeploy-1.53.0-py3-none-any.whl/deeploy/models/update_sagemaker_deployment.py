from typing import Dict, Optional

from deeploy.models import UpdateDeploymentBase


class UpdateSageMakerDeployment(UpdateDeploymentBase):
    """Class that contains the options for updating a SageMaker Deployment"""

    region: Optional[str] = None
    """str, optional: the AWS region used for this Deployment"""
    model_instance_type: Optional[str] = None
    """str, optional: the preferred instance type for the model"""
    explainer_instance_type: Optional[str] = None
    """str, optional: The preferred instance type for the explainer"""
    transformer_instance_type: Optional[str] = None
    """str, optional: The preferred instance type for the explainer"""
    model_config = {
        "protected_namespaces": (),  # For pydantic version 2x need to disable namespace protection for property model_*
    }

    def to_request_body(self) -> Dict:
        request_body = {
            **super().to_request_body(),
            "region": self.region,
            "modelInstanceType": self.model_instance_type,
            "explainerInstanceType": self.explainer_instance_type,
            "transformerInstanceType": self.transformer_instance_type,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        return {k: v for k, v in request_body.items() if v is not None and v != {}}
