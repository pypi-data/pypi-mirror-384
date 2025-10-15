from typing import List, Optional
from warnings import warn

from galtea.utils.from_camel_case_base_model import FromCamelCaseBaseModel


class MetricTypeBase(FromCamelCaseBaseModel):
    """
    **DEPRECATED**
    Use `MetricBase` class instead.
    """

    name: str
    evaluator_model_name: Optional[str] = None
    criteria: Optional[str] = None
    evaluation_steps: Optional[List[str]] = None
    evaluation_params: Optional[List[str]] = None
    judge_prompt: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    description: Optional[str] = None
    documentation_url: Optional[str] = None
    test_type: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warn("MetricTypeBase is deprecated and will be removed in future versions.", DeprecationWarning, stacklevel=2)


class MetricType(MetricTypeBase):
    """
    **DEPRECATED**
    Use `Metric` class instead.
    """

    id: str
    organization_id: Optional[str] = None
    created_at: str
    deleted_at: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warn("MetricType is deprecated and will be removed in future versions.", DeprecationWarning, stacklevel=2)
