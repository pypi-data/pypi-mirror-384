from typing import Optional, Union

from galtea.application.services.product_service import ProductService
from galtea.domain.exceptions.entity_not_found_exception import EntityNotFoundException
from galtea.domain.models.version import Version, VersionBase
from galtea.infrastructure.clients.http_client import Client
from galtea.utils.string import build_query_params, is_valid_id


class VersionService:
    """
    Service for managing Versions.
    A Version is a specific iteration of a product, allowing for tracking improvements and regressions over time.
    """

    def __init__(self, client: Client, product_service: ProductService):
        self._client = client
        self.product_service = product_service

    def version_exists(self, version_name: str) -> bool:
        """
        Check if a version exists by its name.

        Args:
            version_name (str): Name of the version.

        Returns:
            bool: True if the version exists, False otherwise.
        """
        version = self._client.versions(version_name)
        return bool(version)

    def create(
        self,
        product_id: str,
        name: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_id: Optional[str] = None,
        dataset_description: Optional[str] = None,
        dataset_uri: Optional[str] = None,
        endpoint: Optional[str] = None,
        guardrails: Optional[str] = None,
    ) -> Optional[Version]:
        """
        Create a new version for a product. A version represents a specific iteration of a product.

        Args:
            product_id (str): ID of the product to associate the version with.
            name (str): Name for the new version.
            description (str, optional): Version description.
            system_prompt (str, optional): System prompt used for the version.
            model_id (str, optional): Reference to a model configured in the Galtea Platform with cost information.
            dataset_description (str, optional): Description of the dataset used for training.
            dataset_uri (str, optional): URI to the dataset.
            endpoint (str, optional): API endpoint where the version is accessible.
            guardrails (str, optional): Configuration for safety guardrails provided to the model.

        Returns:
            Optional[Version]: The created version object.
        """

        try:
            version = VersionBase(
                name=name,
                product_id=product_id,
                description=description,
                system_prompt=system_prompt,
                model_id=model_id,
                dataset_description=dataset_description,
                dataset_uri=dataset_uri,
                endpoint=endpoint,
                guardrails=guardrails,
            )
            version.model_validate(version.model_dump())
            response = self._client.post("versions", json=version.model_dump(by_alias=True))
            version_response = Version(**response.json())
            return version_response
        except Exception as e:
            print(f"Error creating version {name}: {e}")

    def get(self, version_id: str):
        """
        Retrieve a version by its ID.

        Args:
            version_id (str): ID of the version to retrieve.

        Returns:
            Version: The retrieved version object.
        """
        if not is_valid_id(version_id):
            raise ValueError("Version ID provided is not valid.")

        response = self._client.get(f"versions/{version_id}")
        return Version(**response.json())

    def get_by_name(self, product_id: str, version_name: str):
        """
        Retrieve a version by its name and the product ID it is associated with.

        Args:
            product_id (str): ID of the product.
            version_name (str): Name of the version.

        Returns:
            Version: The retrieved version object.
        """
        if not is_valid_id(product_id):
            raise ValueError("Product ID provided is not valid.")

        query_params = build_query_params(productIds=[product_id], names=[version_name])
        response = self._client.get(f"versions?{query_params}")
        versions = [Version(**version) for version in response.json()]

        if not versions:
            try:
                self.product_service.get(product_id)
            except Exception:
                raise EntityNotFoundException(f"Product with ID {product_id} does not exist.")

        if not versions:
            raise EntityNotFoundException(f"Version with name {version_name} does not exist.")

        return versions[0]

    def list(
        self,
        product_id: Union[str, list[str]],
        sort_by_created_at: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        """
        Get a list of versions for a given product.

        Args:
            product_id (str | list[str]): ID or IDs of the product to retrieve versions from.
            sort_by_created_at (str, optional): Sort by created at. Valid values are 'asc' and 'desc'.
            offset (int, optional): Offset for pagination. This refers to the number of items to skip before
                starting to collect the result set. The default value is 0.
            limit (int, optional): Limit for pagination. This refers to the maximum number of items to collect
                in the result set.

        Returns:
            List[Version]: List of version objects.
        """
        # 1. Validate IDs filter parameters
        product_ids = [product_id] if isinstance(product_id, str) else product_id
        if not all(is_valid_id(product_id) for product_id in product_ids):
            raise ValueError("Product ID provided is not valid.")

        # 2. Validate sort parameters
        if sort_by_created_at is not None and sort_by_created_at not in ["asc", "desc"]:
            raise ValueError("Sort by created at must be 'asc' or 'desc'.")

        query_params = build_query_params(
            productIds=product_ids,
            offset=offset,
            limit=limit,
            sort=["createdAt", sort_by_created_at] if sort_by_created_at else None,
        )
        response = self._client.get(f"versions?{query_params}")
        versions = [Version(**version) for version in response.json()]

        if not versions:
            for product_id in product_ids:
                try:
                    self.product_service.get(product_id)
                except Exception:
                    raise EntityNotFoundException(f"Product with ID {product_id} does not exist.")

        return versions

    def delete(self, version_id: str):
        """
        Delete a version by its ID.

        Args:
            version_id (str): ID of the version to delete.

        Returns:
            None: None.
        """
        if not is_valid_id(version_id):
            raise ValueError("Version ID provided is not valid.")

        self._client.delete(f"versions/{version_id}")
