from typing import Dict, Optional

from pydantic import BaseModel, field_validator

from deeploy.enums.query_param import RHSQuery, SortDirection


class GetRequestLogsOptions(BaseModel):
    """Class that contains the options for retrieving request logs from a Deployment"""

    start: Optional[int] = None
    """int, optional: the start timestamp of the creation of the request log, presented as a unix timestamp in milliseconds"""
    end: Optional[int] = None
    """int, optional: the end timestamp of the creation of the request log, presented as a unix timestamp in milliseconds"""
    offset: Optional[int] = 0
    """int, optional: the offset skips the first request logs for the given offset times the limit"""
    limit: Optional[int] = 10
    """int, optional: the maximum number of request logs to retrieve in one call"""
    sort: Optional[str] = None
    """str, optional: the sorting applied to the retrieved request logs"""
    status: Optional[str] = None
    """str, optional: the status of the request log"""
    commit: Optional[str] = None
    """str, optional: the commit of the request log"""
    status_code: Optional[str] = None
    """str, optional: the status code of the request log"""

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
        "status",
        "commit",
        "status_code",
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
            "status": self.status,
            "commit": self.commit,
            "statusCode": self.status_code,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return {k: v for k, v in params.items() if v is not None and v != {}}
