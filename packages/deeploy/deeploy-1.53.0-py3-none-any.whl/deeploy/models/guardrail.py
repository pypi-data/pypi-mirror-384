from pydantic import BaseModel, ConfigDict

from deeploy.common.functions import to_lower_camel
from deeploy.enums.guardrail_status import GuardrailStatus
from deeploy.enums.guardrail_type import GuardrailType


class Guardrail(BaseModel):
    id: str
    name: str
    guardrail_type: GuardrailType
    apply_to_input: bool
    apply_to_output: bool
    regex: str
    replacement: str | None = "****"
    workspace_id: str
    status: GuardrailStatus
    created_by: str
    last_updated_by: str
    created_at: str
    updated_at: str
    model_config = ConfigDict(alias_generator=to_lower_camel)
