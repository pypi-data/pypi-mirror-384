from typing import Optional

from pydantic import BaseModel, ConfigDict

from deeploy.common.functions import to_lower_camel


class Repository(BaseModel):
    id: str
    team_id: str
    name: str
    status: int
    workspace_id: str
    is_public: Optional[bool] = None
    remote_path: str
    created_at: str
    updated_at: str
    model_config = ConfigDict(alias_generator=to_lower_camel)
