from typing import Optional

from pydantic import BaseModel


class DockerReference(BaseModel):
    image: str
    uri: str
    port: Optional[int] = None


class BlobReference(BaseModel):
    url: str
    region: Optional[str] = None


class MLFlowBlobReference(BaseModel):
    region: str


class MLFlowReference(BaseModel):
    model: str
    alias: Optional[str] = None
    stage: Optional[str] = None
    version: Optional[str] = None
    blob: Optional[MLFlowBlobReference] = None


class AzureMLReference(BaseModel):
    image: str
    uri: str
    port: int
    readiness_path: str
    liveness_path: str
    model: Optional[str] = None
    version: Optional[str] = None


class DatabricksReference(BaseModel):
    model: str
    alias: Optional[str] = None
    version: Optional[str] = None


class ModelReference(BaseModel):
    docker: Optional[DockerReference] = None
    blob: Optional[BlobReference] = None
    mlflow: Optional[MLFlowReference] = None
    azureML: Optional[AzureMLReference] = None
    databricks: Optional[DatabricksReference] = None


class ExplainerReference(BaseModel):
    docker: Optional[DockerReference] = None
    blob: Optional[BlobReference] = None
    mlflow: Optional[MLFlowReference] = None
    azureML: Optional[AzureMLReference] = None
    databricks: Optional[DatabricksReference] = None


class TransformerReference(BaseModel):
    docker: DockerReference
    blob: Optional[BlobReference] = None


class ModelReferenceJson(BaseModel):
    reference: ModelReference


class ExplainerReferenceJson(BaseModel):
    reference: ExplainerReference


class TransformerReferenceJson(BaseModel):
    reference: TransformerReference

class HuggingFaceReference(BaseModel):
    model: str
