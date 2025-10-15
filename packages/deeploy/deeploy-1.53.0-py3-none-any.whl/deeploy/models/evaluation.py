from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from deeploy.common.functions import to_lower_camel


class Evaluation(BaseModel):
    id: str
    agree: bool
    desired_output: Optional[Dict] = None
    comment: Optional[str] = None
    personal_keys_id: Optional[str] = None
    token_id: Optional[str] = None
    oidc_subject_id: Optional[str] = None
    created_at: str
    updated_at: str
    model_config = ConfigDict(alias_generator=to_lower_camel)
