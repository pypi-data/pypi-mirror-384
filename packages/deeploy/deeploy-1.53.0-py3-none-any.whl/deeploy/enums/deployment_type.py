from enum import Enum


class DeploymentType(Enum):
    """Class that contains deployment types"""

    KSERVE = "KServe"
    SAGEMAKER = "Sagemaker"
    AZURE_ML = "AzureML"
    EXTERNAL = "External"
    REGISTRATION = "Registration"
