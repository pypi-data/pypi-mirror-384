from typing import Optional

from pydantic import BaseModel, ConfigDict

from deeploy.common.functions import to_lower_camel


class Workspace(BaseModel):
    id: str
    team_id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    slack_webhook_url: Optional[str] = None
    default_deployment_type: str
    created_at: str
    updated_at: str
    model_config = ConfigDict(alias_generator=to_lower_camel)
