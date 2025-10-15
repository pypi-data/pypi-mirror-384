from typing import List, Optional

from galtea.domain.exceptions.entity_not_found_exception import EntityNotFoundException
from galtea.domain.models.product import Product
from galtea.infrastructure.clients.http_client import Client
from galtea.utils.string import build_query_params, is_valid_id


class ProductService:
    def __init__(self, client: Client):
        self._client = client

    def get(self, product_id: str):
        """
        Retrieve a product by its ID.

        Args:
            product_id (str): ID of the product to retrieve.

        Returns:
            Product: The retrieved product object.
        """
        if not is_valid_id(product_id):
            raise ValueError("Product ID provided is not valid.")

        response = self._client.get(f"products/{product_id}")
        return Product(**response.json())

    def get_by_name(self, name: str):
        """
        Retrieve a product by its name.

        Args:
            name (str): Name of the product to retrieve.

        Returns:
            Product: The retrieved product object.
        """
        query_params = build_query_params(names=[name])
        response = self._client.get(f"products?{query_params}")
        products = [Product(**product) for product in response.json()]

        if not products:
            raise EntityNotFoundException(f"Product with name {name} does not exist.")

        return products[0]

    def delete(self, product_id: str):
        """
        Delete a product by its ID.

        Args:
            product_id (str): ID of the product to delete.

        Returns:
            None: None.
        """
        if not is_valid_id(product_id):
            raise ValueError("Product ID provided is not valid.")

        self._client.delete(f"products/{product_id}")

    def list(
        self, offset: Optional[int] = None, limit: Optional[int] = None, sort_by_created_at: Optional[str] = None
    ) -> List[Product]:
        """
        Get a list of products.

        Args:
            offset (int, optional): Offset for pagination.
            limit (int, optional): Limit for pagination.
            sort_by_created_at (str, optional): Sort by created at. Valid values are 'asc' and 'desc'.

        Returns:
            list[Product]: List of products.
        """
        if sort_by_created_at is not None and sort_by_created_at not in ["asc", "desc"]:
            raise ValueError("Sort by created at must be 'asc' or 'desc'.")

        query_params = build_query_params(
            offset=offset,
            limit=limit,
            sort=["createdAt", sort_by_created_at] if sort_by_created_at else None,
        )
        response = self._client.get(f"products?{query_params}")
        products = [Product(**product) for product in response.json()]
        return products
