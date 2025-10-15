from typing import Dict, Optional, Union

from pydantic import BaseModel, ConfigDict

from deeploy.common.functions import to_lower_camel


class Deployment(BaseModel):
    id: str
    team_id: str
    name: str
    workspace_id: str
    owner_id: str
    public_url: Optional[str] = None
    description: Optional[str] = None
    active_version: Optional[Union[Dict, str]] = None
    updating_to: Optional[Union[Dict, str]] = None
    last_version: Optional[Union[Dict, str]] = None
    use_case: Optional[Union[Dict, str]] = None
    status: int
    created_at: str
    updated_at: str
    model_config = ConfigDict(alias_generator=to_lower_camel)
