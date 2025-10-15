from typing import Dict, List

from pydantic import BaseModel


class CreateActuals(BaseModel):
    """Class that contains the options for creating actuals"""

    prediction_ids: List[str]
    """list: a list of prediction id's for which to upload new actuals"""
    actual_values: List[Dict]
    """list: a list of actuals conform the [data plane v1 format](https://kserve.github.io/website/master/modelserving/data_plane/v1_protocol)
            where the index of the actual value corresponds with the index of the provided prediction log id"""

    def to_request_body(self) -> Dict:
        return {
            "predictionIds": self.prediction_ids,
            "actualValues": self.actual_values,
        }
