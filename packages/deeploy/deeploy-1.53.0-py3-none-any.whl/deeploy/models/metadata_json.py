from typing import List, Optional

from pydantic import BaseModel


class MetadataJson(BaseModel):
    features: Optional[List[dict]] = None
    predictionClasses: Optional[dict] = None
    problemType: Optional[str] = None
    exampleInput: Optional[dict] = None
    exampleOutput: Optional[dict] = None
    inputTensorShape: Optional[str] = None
    outputTensorShape: Optional[str] = None
    customId: Optional[str] = None
