from pydantic import BaseModel, ConfigDict

from deeploy.common.functions import to_lower_camel


class ActualResponse(BaseModel):
    prediction_log_id: str
    status: int
    message: str
    model_config = ConfigDict(alias_generator=to_lower_camel)
