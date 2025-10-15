from typing import Optional

from pydantic import BaseModel

from deeploy.models.reference_json import (
    BlobReference,
    DockerReference,
    TransformerReference,
)


class CreateTransformerReference(BaseModel):
    """Class that contains the options for creating a reference.json for a transformer"""

    docker: Optional[DockerReference] = None
    """DockerReference: docker configuration object of the transformer"""
    blob: Optional[BlobReference] = None
    """BlobReference: blob configuration object of the transformer"""

    def get_reference(self) -> TransformerReference:
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

        if not reference or len(set_properties) == 0:
            raise ValueError("Please provide a valid option")
        elif len(set_properties) > 1:
            allowed_pairs = [
                {"docker", "blob"}
            ]
            
            properties_set = set(set_properties)
            if not any(properties_set.issubset(allowed_pair) for allowed_pair in allowed_pairs):
                raise ValueError(
                    "Invalid combination of properties. Allowed combinations is: "
                    "docker+blob or any single property."
                )

        return reference
