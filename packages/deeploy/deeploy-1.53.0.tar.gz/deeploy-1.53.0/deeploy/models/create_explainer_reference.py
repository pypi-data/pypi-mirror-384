from typing import Optional

from pydantic import BaseModel

from deeploy.models.reference_json import (
    AzureMLReference,
    BlobReference,
    DatabricksReference,
    DockerReference,
    ExplainerReference,
    MLFlowReference,
)


class CreateExplainerReference(BaseModel):
    """Class that contains the options for creating a reference.json for an explainer"""

    docker: Optional[DockerReference] = None
    """DockerReference: docker configuration object of the explainer"""
    blob: Optional[BlobReference] = None
    """BlobReference: blob configuration object of the explainer"""
    mlflow: Optional[MLFlowReference] = None
    """MLFlowReference: mlflow configuration object of the explainer"""
    azure_ml: Optional[AzureMLReference] = None
    """AzureMLReference: azure machine learning configuration object of the explainer"""
    databricks: Optional[DatabricksReference] = None
    """DatabricksReference: databricks unity catalog configuration object of the explainer"""

    def get_reference(self) -> ExplainerReference:
        reference = {}
        set_properties = []
        
        if self.docker:
            reference["docker"] = {
                "image": self.docker.image,
                "uri": self.docker.uri,
                "port": self.docker.port,
            }
            set_properties.append("docker")
        
        if self.blob:
            reference["blob"] = {
                "url": self.blob.url,
                "region": self.blob.region,
            }
            set_properties.append("blob")
            
        if self.mlflow:
            reference["mlflow"] = {
                "model": self.mlflow.model,
                "version": self.mlflow.version,
                "stage": self.mlflow.stage,
                "alias": self.mlflow.alias,
            }
            if self.mlflow.blob and self.mlflow.blob.region:
                reference["mlflow"]["blob"] = {"region": self.mlflow.blob.region}
            set_properties.append("mlflow")
                
        if self.azure_ml:
            reference["azureML"] = {
                "image": self.azure_ml.image,
                "uri": self.azure_ml.uri,
                "port": self.azure_ml.port,
                "readinessPath": self.azure_ml.readiness_path,
                "livenessPath": self.azure_ml.liveness_path,
                "model": self.azure_ml.model,
                "version": self.azure_ml.version,
            }
            set_properties.append("azure_ml")
            
        if self.databricks:
            reference["databricks"] = {
                "model": self.databricks.model,
                "version": self.databricks.version,
                "alias": self.databricks.alias,
            }
            set_properties.append("databricks")

        if not reference or len(set_properties) == 0:
            raise ValueError("Please provide a valid option")
        elif len(set_properties) > 1:
            allowed_pairs = [
                {"docker", "blob"},
                {"docker", "mlflow"},
                {"docker", "databricks"},
            ]
            
            properties_set = set(set_properties)
            if not any(properties_set.issubset(allowed_pair) for allowed_pair in allowed_pairs):
                raise ValueError(
                    "Invalid combination of properties. Allowed combinations are: "
                    "docker+blob, docker+mlflow, docker+databricks, or any single property."
                )

        return reference

