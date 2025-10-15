from typing import Dict, Optional

from deeploy.enums import AutoScalingType
from deeploy.models import UpdateDeploymentBase


class UpdateDeployment(UpdateDeploymentBase):
    """Class that contains the options for updating a Deployment"""

    autoscaling_type: Optional[AutoScalingType] = None
    """int, optional: enum value from AutoScalingType class. Defaults to None (no autoscaling)."""
    model_serverless: Optional[bool] = None
    """bool, optional: whether to deploy the model in a serverless fashion. Defaults to False"""
    model_blob_credentials_id: Optional[str] = None
    """str, optional: uuid of credentials generated in Deeploy to access private Blob storage"""
    model_s3_temporary_access_key_id: Optional[str] = None
    """str, optional: the temporary AWS access key ID to access the model in S3"""
    model_s3_temporary_secret_access_key: Optional[str] = None
    """str, optional: the temporary AWS secret access key to access the model in S3"""
    model_s3_temporary_session_token: Optional[str] = None
    """str, optional: the temporary AWS session token to access the model in S3"""
    model_azure_temporary_sas_token: Optional[str] = None
    """str, optional: the temporary Azure SAS token to access the model in the Azure Blob Storage"""
    model_azure_temporary_storage_account: Optional[str] = None
    """str, optional: the temporary Azure storage account name to access the model in the Azure Blob Storage"""
    model_databricks_temporary_access_token: Optional[str] = None
    """str, optional: the temporary Databricks access token to access the model in the Databricks Unity Catalog"""
    model_docker_credentials_id: Optional[str] = None
    """str, optional: uuid of credentials generated in Deeploy to access private Docker repo"""
    model_docker_temporary_registry: Optional[str] = None
    """str, optional: the temporary Docker registry to pull the models custom Docker image"""
    model_docker_temporary_username: Optional[str] = None
    """str, optional: the temporary Docker username to pull the models custom Docker image"""
    model_docker_temporary_password: Optional[str] = None
    """str, optional: the temporary Docker password to pull the models custom Docker image"""
    model_instance_type: Optional[str] = None
    """str, optional: the preferred instance type for the model"""
    model_mem_request: Optional[int] = None
    """int, optional: RAM request of model pod, in Megabytes."""
    model_mem_limit: Optional[int] = None
    """int, optional: RAM limit of model pod, in Megabytes."""
    model_cpu_request: Optional[float] = None
    """float, optional: CPU request of model pod, in number of cores."""
    model_cpu_limit: Optional[float] = None
    """float, optional: CPU limit of model pod, in number of cores."""
    model_gpu_request: Optional[float] = None
    """float, optional: GPU request of model pod, in number of GPUs."""
    model_environment_variable_ids: Optional[list] = None
    """list, optional: environment variable IDs of which the key and value will be passed to the model container as environment variables"""
    model_args: Optional[dict] = None
    """dict, optional: arguments to pass to model container key is argument name, value is argument value"""
    explainer_serverless: Optional[bool] = None
    """bool, optional: whether to deploy the explainer in a serverless fashion. Defaults to False"""
    explainer_blob_credentials_id: Optional[str] = None
    """str, optional: Credential id of credential generated in Deeploy to access private Blob storage"""
    explainer_s3_temporary_access_key_id: Optional[str] = None
    """str, optional: the temporary AWS access key ID to access the explainer in S3"""
    explainer_s3_temporary_secret_access_key: Optional[str] = None
    """str, optional: the temporary AWS secret access key to access the explainer in S3"""
    explainer_s3_temporary_session_token: Optional[str] = None
    """str, optional: the temporary AWS session token to access the explainer in S3"""
    explainer_azure_temporary_sas_token: Optional[str] = None
    """str, optional: the temporary Azure SAS token to access the explainer in the Azure Blob Storage"""
    explainer_azure_temporary_storage_account: Optional[str] = None
    """str, optional: the temporary Azure storage account name to access the explainer in the Azure Blob Storage"""
    explainer_databricks_temporary_access_token: Optional[str] = None
    """str, optional: the temporary Databricks access token to access the explainer in the Databricks Unity Catalog"""
    explainer_docker_credentials_id: Optional[str] = None
    """str, optional: Credential id of credential generated in Deeploy to access private Docker repo"""
    explainer_docker_temporary_registry: Optional[str] = None
    """str, optional: the temporary Docker registry to pull the explainers custom Docker image"""
    explainer_docker_temporary_username: Optional[str] = None
    """str, optional: the temporary Docker username to pull the explainers custom Docker image"""
    explainer_docker_temporary_password: Optional[str] = None
    """str, optional: the temporary Docker password to pull the explainers custom Docker image"""
    explainer_instance_type: Optional[str] = None
    """str, optional: The preferred instance type for the explainer pod."""
    explainer_mem_request: Optional[int] = None
    """int, optional: RAM request of explainer pod, in Megabytes."""
    explainer_mem_limit: Optional[int] = None
    """int, optional: RAM limit of explainer pod, in Megabytes."""
    explainer_cpu_request: Optional[float] = None
    """float, optional: CPU request of explainer pod, in number of cores."""
    explainer_cpu_limit: Optional[float] = None
    """float, optional: CPU limit of explainer pod, in number of cores."""
    explainer_gpu_request: Optional[float] = None
    """float, optional: GPU request of explainer pod, in number of GPUs."""
    explainer_environment_variable_ids: Optional[list] = None
    """list, optional: environment variable IDs of which the key and value will be passed to the modelexplainercontainer as environment variables"""
    explainer_args: Optional[dict] = None
    """dict, optional: arguments to pass to explainer container key is argument name, value is argument value"""
    transformer_serverless: Optional[bool] = None
    """bool, optional: whether to deploy the transformer in a serverless fashion. Defaults to False"""
    transformer_docker_credentials_id: Optional[str] = None
    """str, optional: Credential id of credential generated in Deeploy to access private Docker repo"""
    transformer_docker_temporary_registry: Optional[str] = None
    """str, optional: the temporary Docker registry to pull the transformers custom Docker image"""
    transformer_docker_temporary_username: Optional[str] = None
    """str, optional: the temporary Docker username to pull the transformers custom Docker image"""
    transformer_docker_temporary_password: Optional[str] = None
    """str, optional: the temporary Docker password to pull the transformers custom Docker image"""
    transformer_instance_type: Optional[str] = None
    """str, optional: The preferred instance type for the transformer pod."""
    transformer_mem_request: Optional[int] = None
    """int, optional: RAM request of transformer pod, in Megabytes."""
    transformer_mem_limit: Optional[int] = None
    """int, optional: RAM limit of transformer pod, in Megabytes."""
    transformer_cpu_request: Optional[float] = None
    """float, optional: CPU request of transformer pod, in number of cores."""
    transformer_cpu_limit: Optional[float] = None
    """float, optional: CPU limit of transformer pod, in number of cores."""
    transformer_gpu_request: Optional[float] = None
    """float, optional: GPU request of transformer pod, in number of GPUs."""
    transformer_environment_variable_ids: Optional[list] = None
    """list, optional: environment variable IDs of which the key and value will be passed to the transformer container as environment variables"""
    transformer_args: Optional[dict] = None
    """dict, optional: arguments to pass to transformer container key is argument name, value is argument value"""

    model_config = {
        "protected_namespaces": (),  # For pydantic version 2x need to disable namespace protection for property model_*
    }

    def to_request_body(self) -> Dict:
        request_body = {
            **super().to_request_body(),
            "autoScalingType": getattr(self.autoscaling_type, "value", None),
            "modelServerless": self.model_serverless,
            "modelBlobCredentialsId": self.model_blob_credentials_id,
            "modelS3TemporaryAccessKeyId": self.model_s3_temporary_access_key_id,
            "modelS3TemporarySecretAccessKey": self.model_s3_temporary_secret_access_key,
            "modelS3TemporarySessionToken": self.model_s3_temporary_session_token,
            "modelAzureTemporarySasToken": self.model_azure_temporary_sas_token,
            "modelAzureTemporaryStorageAccount": self.model_azure_temporary_storage_account,
            "modelDatabricksTemporaryAccessToken": self.model_databricks_temporary_access_token,
            "modelDockerCredentialsId": self.model_docker_credentials_id,
            "modelDockerTemporaryRegistry": self.model_docker_temporary_registry,
            "modelDockerTemporaryUsername": self.model_docker_temporary_username,
            "modelDockerTemporaryPassword": self.model_docker_temporary_password,
            "modelInstanceType": self.model_instance_type,
            "modelMemRequest": self.model_mem_request,
            "modelMemLimit": self.model_mem_limit,
            "modelCpuRequest": self.model_cpu_request,
            "modelCpuLimit": self.model_cpu_limit,
            "modelGpuRequest": self.model_gpu_request,
            "modelEnvironmentVariableIds": self.model_environment_variable_ids,
            "modelArgs": self.model_args,
            "explainerServerless": self.explainer_serverless,
            "explainerInstanceType": self.explainer_instance_type,
            "explainerBlobCredentialsId": self.explainer_blob_credentials_id,
            "explainerS3TemporaryAccessKeyId": self.explainer_s3_temporary_access_key_id,
            "explainerS3TemporarySecretAccessKey": self.explainer_s3_temporary_secret_access_key,
            "explainerS3TemporarySessionToken": self.explainer_s3_temporary_session_token,
            "explainerAzureTemporarySasToken": self.explainer_azure_temporary_sas_token,
            "explainerAzureTemporaryStorageAccount": self.explainer_azure_temporary_storage_account,
            "explainerDatabricksTemporaryAccessToken": self.explainer_databricks_temporary_access_token,
            "explainerDockerCredentialsId": self.explainer_docker_credentials_id,
            "explainerDockerTemporaryRegistry": self.explainer_docker_temporary_registry,
            "explainerDockerTemporaryUsername": self.explainer_docker_temporary_username,
            "explainerDockerTemporaryPassword": self.explainer_docker_temporary_password,
            "explainerMemRequest": self.explainer_mem_request,
            "explainerMemLimit": self.explainer_mem_limit,
            "explainerCpuRequest": self.explainer_cpu_request,
            "explainerCpuLimit": self.explainer_cpu_limit,
            "explainerGpuRequest": self.explainer_gpu_request,
            "explainerEnvironmentVariableIds": self.explainer_environment_variable_ids,
            "explainerArgs": self.explainer_args,
            "transformerServerless": self.transformer_serverless,
            "transformerBlobCredentialsId": None,
            "transformerDockerCredentialsId": self.transformer_docker_credentials_id,
            "transformerDockerTemporaryRegistry": self.explainer_docker_temporary_registry,
            "transformerDockerTemporaryUsername": self.explainer_docker_temporary_username,
            "transformerDockerTemporaryPassword": self.explainer_docker_temporary_password,
            "transformerInstanceType": self.transformer_instance_type,
            "transformerMemRequest": self.transformer_mem_request,
            "transformerMemLimit": self.transformer_mem_limit,
            "transformerCpuRequest": self.transformer_cpu_request,
            "transformerCpuLimit": self.transformer_cpu_limit,
            "transformerGpuRequest": self.transformer_gpu_request,
            "transformerEnvironmentVariableIds": self.transformer_environment_variable_ids,
            "transformerArgs": self.transformer_args,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        return {k: v for k, v in request_body.items() if v is not None and v != {}}
