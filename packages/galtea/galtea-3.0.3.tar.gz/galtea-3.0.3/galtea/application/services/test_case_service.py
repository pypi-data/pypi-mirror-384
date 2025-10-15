from typing import Optional, Union

from galtea.application.services.test_service import TestService
from galtea.domain.exceptions.entity_not_found_exception import EntityNotFoundException
from galtea.domain.models.test_case import TestCase, TestCaseBase
from galtea.infrastructure.clients.http_client import Client
from galtea.utils.string import build_query_params, is_valid_id


class TestCaseService:
    def __init__(self, client: Client, test_service: TestService):
        self._client = client
        self.test_service = test_service

    def create(
        self,
        test_id: str,
        input: Optional[str] = None,
        expected_output: Optional[str] = None,
        context: Optional[str] = None,
        variant: Optional[str] = None,
        user_persona: Optional[str] = None,
        scenario: Optional[str] = None,
        goal: Optional[str] = None,
        stopping_criterias: Optional[list[str]] = None,
        initial_prompt: Optional[str] = None,
        reviewed_by_id: Optional[str] = None,
        language: Optional[str] = None,
        user_score: Optional[int] = None,
        user_score_reason: Optional[str] = None,
        confidence: Optional[float] = None,
        confidence_reason: Optional[str] = None,
    ) -> TestCase:
        """
        Create a new test case.

        Args:
            test_id (str): ID of the test.
            input (str): Input for the test case.
            expected_output (Optional[str], optional): Expected output for the test case.
            context (Optional[str], optional): Context for the test case.
            variant (Optional[str], optional): Variant for the test case.
            user_persona (Optional[str], optional): User persona for the test case.
            scenario (Optional[str], optional): Scenario for the test case.
            goal (Optional[str], optional): Goal for the test case.
            stopping_criterias (Optional[list[str]], optional): Stopping criteria for the test case.
            initial_prompt (Optional[str], optional): Initial prompt for the test case.
            reviewed_by_id (Optional[str], optional): ID of the user who reviewed the test case.
            language (Optional[str], optional): Language for the test case.\n
                Follow this list to know the supported ones:
                - https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes
            user_score (Optional[int], optional): User vote for the test case (1 for good quality, -1 for bad quality,
                0 for unreviewed).
            user_score_reason (Optional[str], optional): Reason for the user vote given.
            confidence (Optional[float], optional): Confidence for the test case.
            confidence_reason (Optional[str], optional): Reason for the confidence given.

        Returns:
            TestCase: The created test case object.
        """
        test_case: TestCaseBase = TestCaseBase(
            test_id=test_id,
            input=input,
            expected_output=expected_output,
            context=context,
            variant=variant,
            user_persona=user_persona,
            scenario=scenario,
            goal=goal,
            stopping_criterias=stopping_criterias,
            initial_prompt=initial_prompt,
            reviewed_by_id=reviewed_by_id,
            language_code=language,
            user_score=user_score,
            user_score_reason=user_score_reason,
            confidence=confidence,
            confidence_reason=confidence_reason,
        )
        test_case.model_validate(test_case.model_dump())
        response = self._client.post("testCases", json=test_case.model_dump(by_alias=True))
        test_case_response: TestCase = TestCase(**response.json())
        return test_case_response

    def list(
        self,
        test_id: Union[str, list[str]],
        languages: Optional[list[str]] = None,
        variants: Optional[list[str]] = None,
        strategies: Optional[list[str]] = None,
        reviewed: Optional[bool] = None,
        user_score: Optional[int] = None,
        sort_by_created_at: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        """
        Retrieve test cases for a given test ID.

        Args:
            test_id (str | list[str]): ID or list of IDs of the test(s) to retrieve test cases from.
            languages (list[str], optional): List of languages to filter by.
                Follow this list to know the supported ones:
                - https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes
            variants (list[str], optional): List of variants to filter by.
            strategies (list[str], optional): List of strategies to filter by.
            reviewed (bool, optional): Filter by reviewed status.
            user_score (int, optional): Filter by user score (0 for unreviewed, 1 for good quality, -1 for bad quality).
            sort_by_created_at (str, optional): Sort by created at. Valid values are 'asc' and 'desc'.
            offset (int, optional): Offset for pagination. This refers to the number of items to skip before
                starting to collect the result set. The default value is 0.
            limit (int, optional): Limit for pagination. This refers to the maximum number of items to collect
                in the result set.

        Returns:
            list[TestCase]: List of test case objects.
        """
        # 1. Validate IDs filter parameters
        test_ids = [test_id] if isinstance(test_id, str) else test_id
        if not all(is_valid_id(test_id) for test_id in test_ids):
            raise ValueError("Test ID provided is not valid.")

        # 2. Validate sort parameters
        if sort_by_created_at is not None and sort_by_created_at not in ["asc", "desc"]:
            raise ValueError("Sort by created at must be 'asc' or 'desc'.")

        query_params = build_query_params(
            testIds=test_ids,
            reviewed=reviewed,
            userScore=user_score,
            languages=languages,
            variants=variants,
            strategies=strategies,
            offset=offset,
            limit=limit,
            sort=["createdAt", sort_by_created_at] if sort_by_created_at else None,
        )
        response = self._client.get(f"testCases?{query_params}")
        test_cases = [TestCase(**test_case) for test_case in response.json()]

        if not test_cases:
            try:
                self.test_service.get(test_id)
            except Exception:
                raise EntityNotFoundException(f"Test with ID {test_id} does not exist.")

        return test_cases

    def get(self, test_case_id: str):
        """
        Retrieve a test case by its ID.

        Args:
            test_case_id (str): ID of the test case.

        Returns:
            TestCase: The retrieved test case object.
        """
        if not is_valid_id(test_case_id):
            raise ValueError("Test case ID provided is not valid.")

        response = self._client.get(f"testCases/{test_case_id}")
        test_case_response = TestCase(**response.json())
        return test_case_response

    def delete(self, test_case_id: str):
        """
        Delete a test case by its ID.

        Args:
            test_case_id (str): ID of the test case to be deleted.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        if not is_valid_id(test_case_id):
            raise ValueError("Test case ID provided is not valid.")

        self._client.delete(f"testCases/{test_case_id}")
