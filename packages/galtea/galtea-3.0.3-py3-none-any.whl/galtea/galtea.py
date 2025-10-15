import warnings
from typing import Final

from galtea.application.services.conversation_simulator_service import ConversationSimulatorService
from galtea.application.services.evaluation_service import EvaluationService
from galtea.application.services.evaluation_task_service import EvaluationTaskService
from galtea.application.services.inference_result_service import InferenceResultService
from galtea.application.services.metric_service import MetricService
from galtea.application.services.metric_type_service import MetricTypeService
from galtea.application.services.product_service import ProductService
from galtea.application.services.session_service import SessionService
from galtea.application.services.simulator_service import SimulatorService
from galtea.application.services.test_case_service import TestCaseService
from galtea.application.services.test_service import TestService
from galtea.application.services.version_service import VersionService
from galtea.infrastructure.clients.http_client import Client
from galtea.utils.validate_installed_version import validate_installed_version


class Galtea:
    def __init__(self, api_key: str, suppress_updatable_version_message: bool = False):
        """Initialize the Galtea SDK with the provided API key.
        Args:
            api_key (str): The API key to access the Galtea platform for authentication.
            suppress_updatable_version_message (bool): If True, suppresses the message about a newer version available.
        """
        self.__client: Final = Client(api_key)
        self.products: Final = ProductService(self.__client)
        self.tests: Final = TestService(self.__client, self.products)
        self.test_cases: Final = TestCaseService(self.__client, self.tests)
        self.versions: Final = VersionService(self.__client, self.products)
        self.metrics: Final = MetricService(self.__client)
        self.sessions: Final = SessionService(self.__client, self.test_cases, self.tests, self.versions)
        self.inference_results: Final = InferenceResultService(self.__client, self.sessions)
        self.evaluations: Final = EvaluationService(
            self.__client,
            self.metrics,
            self.sessions,
            self.test_cases,
            self.tests,
            self.versions,
        )
        self.conversation_simulator: Final = ConversationSimulatorService(self.__client)
        self.simulator: Final = SimulatorService(
            self.__client,
            self.sessions,
            self.test_cases,
            self.inference_results,
            self.conversation_simulator,
        )

        # DEPRECATED: Use `self.metrics` and `self.evaluations` instead.
        self.__metric_types: Final = MetricTypeService(self.__client)
        self.__evaluation_tasks: Final = EvaluationTaskService(
            self.__client,
            self.evaluations,
            self.__metric_types,
            self.sessions,
            self.test_cases,
        )

        # Validate that the installed version of the SDK is compatible with the API
        validate_installed_version(self.__client, suppress_updatable_version_message)

    @property
    def metric_types(self) -> MetricTypeService:
        warnings.warn(
            (
                "galtea.metric_types is deprecated and will be removed in a future release.\n"
                "Use galtea.metrics API instead."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__metric_types

    @metric_types.setter
    def metric_types(self, value: MetricTypeService) -> None:
        warnings.warn(
            (
                "galtea.metric_types is deprecated and will be removed in a future release.\n"
                "Use galtea.metrics API instead."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        self.__metric_types = value

    @property
    def evaluation_tasks(self) -> EvaluationTaskService:
        warnings.warn(
            (
                "galtea.evaluation_tasks is deprecated and will be removed in a future release.\n"
                "Use galtea.evaluations API instead."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__evaluation_tasks

    @evaluation_tasks.setter
    def evaluation_tasks(self, value: EvaluationTaskService) -> None:
        warnings.warn(
            (
                "galtea.evaluation_tasks is deprecated and will be removed in a future release.\n"
                "Use galtea.evaluations API instead."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        self.__evaluation_tasks = value
