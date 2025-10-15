from typing import Optional

from galtea.utils.from_camel_case_base_model import FromCamelCaseBaseModel


class Evaluation(FromCamelCaseBaseModel):
    id: str
    metric_id: str
    session_id: Optional[str] = None
    score: Optional[float] = None
    reason: Optional[str] = None
    status: str
    conversation_simulator_version: Optional[str] = None
    created_at: str
    deleted_at: Optional[str] = None
    evaluated_at: Optional[str] = None
