from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from deeploy.common.functions.functions import to_lower_camel
from deeploy.enums.inference_endpoint import InferenceEndpoint


class JobSchedule(BaseModel):
    id: str
    name: str
    cron_expression: str
    deployment: Optional[Dict] = None
    workspace_id: str
    endpoint: InferenceEndpoint
    active: bool
    last_run_successful: Optional[bool] = None
    last_run_at: Optional[str] = None
    created_by: str
    created_at: str
    last_updated_by: str
    updated_at: str
    model_config = ConfigDict(alias_generator=to_lower_camel)
