from typing import Dict, Optional

from pydantic import BaseModel, field_validator

from deeploy.enums.query_param import RHSQuery, SortDirection


class GetPredictionLogsOptions(BaseModel):
    """Class that contains the options for retrieving prediction logs from a Deployment"""

    start: Optional[int] = None
    """int, optional: the start timestamp of the creation of the prediction log, presented as a unix timestamp in milliseconds"""
    end: Optional[int] = None
    """int, optional: the end timestamp of the creation of the prediction log, presented as a unix timestamp in milliseconds"""
    offset: Optional[int] = 0
    """int, optional: the offset skips the first prediction logs for the given offset times the limit"""
    limit: Optional[int] = 10
    """int, optional: the maximum number of prediction logs to retrieve in one call"""
    sort: Optional[str] = None
    """str, optional: the sorting applied to the retrieved prediction logs"""
    custom_id: Optional[str] = None
    """str, optional: the custom ID associated to the prediction logs"""
    request_log_id: Optional[str] = None
    """str, optional: the uuid of the request log"""
    id: Optional[str] = None
    """str, optional: the uuid of the prediction log"""
    prediction_class: Optional[str] = None
    """str, optional: the prediction class from your metadata.json used to filter the prediction logs based on the value of their response body"""
    actual: Optional[str] = None
    """str, optional: whether the actual is available on the prediction log"""
    evaluation: Optional[str] = None
    """str, optional: the evaluation status of the prediction log"""
    status: Optional[str] = None
    """str, optional: the status of the request log of the prediction log"""
    endpoint_type: Optional[str] = None
    """str, optional: the endpoint type of the prediction log"""

    @field_validator("sort")
    @classmethod
    def sort_must_follow_rhs_syntax(cls, value: str) -> str:
        if ":" not in value:
            raise ValueError("sort must contain a colon (:)")

        if len(value.split(":")) != 2:
            raise ValueError("sort contains too many colons")

        [left_of_colon, right_of_colon] = value.split(":")

        if right_of_colon not in SortDirection:
            raise ValueError("invalid sort direction")

        return value

    @field_validator(
        "custom_id",
        "prediction_class",
        "actual",
        "evaluation",
        "status",
        "request_log_id",
        "id",
        "endpoint_type",
    )
    @classmethod
    def must_be_valid_rhs_syntax(cls, value: str) -> str:
        if ":" not in value:
            raise ValueError("must contain a colon (:)")

        if len(value.split(":")) != 2:
            raise ValueError("contains too many colons")

        [left_of_colon, right_of_colon] = value.split(":")

        if left_of_colon not in RHSQuery:
            raise ValueError("invalid RHS operator")

        return value

    def to_params(self) -> Dict:
        params = {
            "start": self.start,
            "end": self.end,
            "offset": self.offset,
            "limit": self.limit,
            "sort": self.sort,
            "customId": self.custom_id,
            "requestLogId": self.request_log_id,
            "predictionClass": self.prediction_class,
            "actual": self.actual,
            "evaluation": self.evaluation,
            "status": self.status,
            "id": self.id,
            "endpointType": self.endpoint_type,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return {k: v for k, v in params.items() if v is not None and v != {}}
