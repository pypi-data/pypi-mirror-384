from typing import Optional
from warnings import warn

from pydantic import Field

from galtea.utils.from_camel_case_base_model import FromCamelCaseBaseModel


class EvaluationTask(FromCamelCaseBaseModel):
    """
    **DEPRECATED**
    Use `Evaluation` class instead.
    """

    id: str
    metric_type_id: str = Field(alias="metricId")
    score: Optional[float] = None
    status: str
    conversation_simulator_version: Optional[str] = None
    created_at: str
    deleted_at: Optional[str] = None
    evaluated_at: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warn("EvaluationTask is deprecated and will be removed in future versions.", DeprecationWarning, stacklevel=2)
