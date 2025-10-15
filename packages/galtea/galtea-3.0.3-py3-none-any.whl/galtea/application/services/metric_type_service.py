from typing import List, Optional

from galtea.domain.exceptions.entity_not_found_exception import EntityNotFoundException
from galtea.domain.models.metric_type import MetricType, MetricTypeBase
from galtea.infrastructure.clients.http_client import Client
from galtea.utils.string import build_query_params, is_valid_id


class MetricTypeService:
    """
    Service for managing Metric Types.
    A Metric Type defines a way to evaluate and score product performance.
    """

    def __init__(self, client: Client):
        self._client = client

    def create(
        self,
        name: str,
        test_type: str,
        evaluator_model_name: Optional[str] = None,
        judge_prompt: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        documentation_url: Optional[str] = None,
    ):
        """
        Create a new metric type.

        Args:
            name (str): Name of the metric type.
            test_type (str): The type of test this metric is designed for.
                Possible values: `QUALITY`, `RED_TEAMING`, `SCENARIOS`.
            evaluator_model_name (str, optional): Name of the model to use for evaluation.
                Required for "LLM as a Judge" metrics.
                See https://docs.galtea.ai/sdk/api/metrics/create#param-evaluator-model-name for available models.
            judge_prompt (str, optional): Custom prompt for the judge model. This defines an "LLM as a Judge"
                metric. Placeholders for product and test case information can be used.
            tags (list[str], optional): Tags to help categorize and organize the metric type.
            description (str, optional): Description of the metric type.
            documentation_url (str, optional): Documentation URL for the metric type.

        Returns:
            Optional[Metric]: The created metric type object, or None if an error occurs.
        """
        try:
            metric_type = MetricTypeBase(
                name=name,
                test_type=test_type,
                evaluator_model_name=evaluator_model_name,
                judge_prompt=judge_prompt,
                tags=tags,
                description=description,
                documentation_url=documentation_url,
            )

            metric_type.model_validate(metric_type.model_dump())
            response = self._client.post("metrics", json=metric_type.model_dump(by_alias=True))
            metric_type_response = MetricType(**response.json())
            return metric_type_response
        except Exception as e:
            print(f"Error creating Metric Type: {e}")
            return None

    def get(self, metric_type_id: str):
        """
        Retrieve a metric type by its ID.

        Args:
            metric_type_id (str): ID of the metric type to retrieve.

        Returns:
            Metric: The retrieved metric type object.
        """
        if not is_valid_id(metric_type_id):
            raise ValueError("Metric type ID provided is not valid.")

        response = self._client.get(f"metrics/{metric_type_id}")
        return MetricType(**response.json())

    def get_by_name(self, name: str):
        """
        Retrieve a metric type by its name.

        Args:
            name (str): Name of the metric type to retrieve.

        Returns:
            Metric: The retrieved metric type object.
        """
        query_params = build_query_params(names=[name])
        response = self._client.get(f"metrics?{query_params}")
        metricTypes = [MetricType(**metric_type) for metric_type in response.json()]

        if not metricTypes:
            raise EntityNotFoundException(f"Metric type with name {name} does not exist.")

        return metricTypes[0]

    def delete(self, metric_type_id: str):
        """
        Delete a metric type by its ID.

        Args:
            metric_type_id (str): ID of the metric type to delete.

        Returns:
            None: None.
        """
        if not is_valid_id(metric_type_id):
            raise ValueError("Metric type ID provided is not valid.")

        self._client.delete(f"metrics/{metric_type_id}")

    def list(self, offset: Optional[int] = None, limit: Optional[int] = None) -> List[MetricType]:
        """
        Get a list of metric types.

        Args:
            offset (int, optional): Offset for pagination.
            limit (int, optional): Limit for pagination.

        Returns:
            List[Metric]: List of metric types.
        """
        query_params = build_query_params(offset=offset, limit=limit)
        response = self._client.get(f"metrics?{query_params}")
        metric_types = [MetricType(**metric_type) for metric_type in response.json()]
        return metric_types
