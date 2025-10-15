from typing import List, Optional

from galtea.domain.exceptions.entity_not_found_exception import EntityNotFoundException
from galtea.domain.models.metric import Metric, MetricBase
from galtea.infrastructure.clients.http_client import Client
from galtea.utils.string import build_query_params, is_valid_id


class MetricService:
    """
    Service for managing Metrics.
    A Metric defines a way to evaluate and score product performance.
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
        Create a new metric.

        Args:
            name (str): Name of the metric.
            test_type (str): The type of test this metric is designed for.
                Possible values: `QUALITY`, `RED_TEAMING`, `SCENARIOS`.
            evaluator_model_name (str, optional): Name of the model to use for evaluation.
                Required for "LLM as a Judge" metrics.
                See https://docs.galtea.ai/sdk/api/metrics/create#param-evaluator-model-name for available models.
            judge_prompt (str, optional): Custom prompt for the judge model. This defines an "LLM as a Judge"
                metric. Placeholders for product and test case information can be used.
            tags (list[str], optional): Tags to help categorize and organize the metric.
            description (str, optional): Description of the metric.
            documentation_url (str, optional): Documentation URL for the metric.

        Returns:
            Optional[Metric]: The created metric object, or None if an error occurs.
        """
        try:
            metric = MetricBase(
                name=name,
                test_type=test_type,
                evaluator_model_name=evaluator_model_name,
                judge_prompt=judge_prompt,
                tags=tags,
                description=description,
                documentation_url=documentation_url,
            )

            metric.model_validate(metric.model_dump())
            response = self._client.post("metrics", json=metric.model_dump(by_alias=True))
            metric_response = Metric(**response.json())
            return metric_response
        except Exception as e:
            print(f"Error creating Metric: {e}")
            return None

    def get(self, metric_id: str):
        """
        Retrieve a metric by its ID.

        Args:
            metric_id (str): ID of the metric to retrieve.

        Returns:
            Metric: The retrieved metric object.
        """
        if not is_valid_id(metric_id):
            raise ValueError("Metric ID provided is not valid.")

        response = self._client.get(f"metrics/{metric_id}")
        return Metric(**response.json())

    def get_by_name(self, name: str):
        """
        Retrieve a metric by its name.

        Args:
            name (str): Name of the metric to retrieve.

        Returns:
            Metric: The retrieved metric object.
        """
        query_params = build_query_params(names=[name])
        response = self._client.get(f"metrics?{query_params}")
        metrics = [Metric(**metric) for metric in response.json()]

        if not metrics:
            raise EntityNotFoundException(f"Metric with name {name} does not exist.")

        return metrics[0]

    def delete(self, metric_id: str):
        """
        Delete a metric by its ID.

        Args:
            metric_id (str): ID of the metric to delete.

        Returns:
            None: None.
        """
        if not is_valid_id(metric_id):
            raise ValueError("Metric ID provided is not valid.")

        self._client.delete(f"metrics/{metric_id}")

    def list(
        self, offset: Optional[int] = None, limit: Optional[int] = None, sort_by_created_at: Optional[str] = None
    ) -> List[Metric]:
        """
        Get a list of metrics.

        Args:
            offset (int, optional): Offset for pagination.
            limit (int, optional): Limit for pagination.
            sort_by_created_at (str, optional): Sort by created at. Valid values are 'asc' and 'desc'.

        Returns:
            List[Metric]: List of metrics.
        """
        if sort_by_created_at is not None and sort_by_created_at not in ["asc", "desc"]:
            raise ValueError("Sort by created at must be 'asc' or 'desc'.")

        query_params = build_query_params(
            offset=offset,
            limit=limit,
            sort=["createdAt", sort_by_created_at] if sort_by_created_at else None,
        )
        response = self._client.get(f"metrics?{query_params}")
        metrics = [Metric(**metric) for metric in response.json()]
        return metrics
