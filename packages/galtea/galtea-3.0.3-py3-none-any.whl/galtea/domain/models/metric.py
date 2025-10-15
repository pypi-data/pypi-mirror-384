from typing import List, Optional

from galtea.utils.from_camel_case_base_model import FromCamelCaseBaseModel


class MetricBase(FromCamelCaseBaseModel):
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


class Metric(MetricBase):
    id: str
    organization_id: Optional[str] = None
    created_at: str
    deleted_at: Optional[str] = None
