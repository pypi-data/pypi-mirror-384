from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Tuple

from nys_constants.nys_constants import OnEmptySKUAction, MeasurementUnit, SortOrder
from nys_schemas.sku_schema import (
    Sku,
    SkuCreate,
    SkuResponse,
    SkuFilter,
    SkuPatch,
    SkuSort,
)

from .base import BaseResource

__all__ = [
    'SkuResource',  # The main resource class
    'Sku',
    'SkuCreate',
    'SkuResponse',
    'SkuFilter',
    'SkuPatch',
    'SkuSort',
    'SortOrder',
    'OnEmptySKUAction',
    'MeasurementUnit',
]

class SkuResource(BaseResource[SkuResponse]):
    """Resource for interacting with SKUs."""

    def create(
        self,
        sku: SkuCreate
    ) -> SkuResponse:
        """
        Create a new SKU with the specified parameters.
        
        Args:
            sku: SkuCreate object containing the SKU parameters
            
        Returns:
            Sku: The created SKU object
            
        Example:
            >>> from nys_client.skus import MeasurementUnit
            >>> client.skus.create(
            ...     sku=SkuCreate(
            ...         id="SKU123",
            ...         name="Test SKU",
            ...         description="A test SKU",
            ...         measurement_unit=MeasurementUnit.PIECES
            ...     )
            ... )
        """

        
        response = self._client._request(
            method="POST",
            endpoint="api/v2/sku",
            json=sku.dict(exclude_unset=True)
        )
        
        return SkuResponse(**response.json())

    def search(
        self,
        *,
        filters: Optional[Union[Dict[str, Any], SkuFilter]] = None,
        search: Optional[str] = None,
        sort_by: Optional[Union[str, List[Tuple[SkuSort, SortOrder]]]] = None,
        page: int = 1,
        size: int = 50
    ) -> List[SkuResponse]:
        """
        Search and filter SKUs.
        
        Args:
            filters: SKU-specific filters. Can be either:
                - A SkuFilter instance with fields like id__eq, name__ilike, etc.
                - A dict matching the SkuFilter schema
            search: Search query string to filter SKUs.
                - Field-specific search: field:value (e.g., id:tee)
                - Logical operators: AND, OR
                - Grouping with parentheses
                - Results will be ordered by the greatest trigram similarity among all the specified field:value pairs
                - Example: "id:tee OR name:Tee"
            sort_by: a list of tuples of (SkuSort, SortOrder) or a string representing the sort order.
                - Example: [(SkuSort.TOTAL_QUANTITY, SortOrder.DESC)]
                - Example: "-created_at" (for descending order)
            page: Page number (1-based, default: 1)
            size: Items per page (default: 50)
            
        Returns:
            List[SkuResponse]: List of SKUs matching the filters
            
        Examples:
            >>> # Search using a dictionary filter
            >>> from nys_client.skus import MeasurementUnit, SkuSort
            >>> client.skus.search(
            ...     filters={"measurement_unit__in": [MeasurementUnit.PIECE, MeasurementUnit.GRAM]},
            ...     search="id:Tee OR name:Tee",
            ...     sort_by=[(SkuSort.CREATED_AT, SortOrder.DESC)]
            ... )

            >>> # Search using SkuFilter (recommended)
            >>> from nys_client.skus import SkuFilter, MeasurementUnit, SkuSort
            >>> client.skus.search(
            ...     filters=SkuFilter(
            ...         measurement_unit__in=[MeasurementUnit.PIECE, MeasurementUnit.GRAM],
            ...         name__ilike="test"
            ...     ),
            ...     sort_by=[(SkuSort.CREATED_AT, SortOrder.DESC)]
            ... )
        """
        if isinstance(filters, dict):
            filters = SkuFilter(**filters)

        return self._search(
            endpoint="api/v2/skus",
            response_model=SkuResponse,
            filters=filters,
            search=search,
            sort_by=sort_by,
            page=page,
            size=size
        )

    def patch(
        self,
        sku_id: str,
        patch: SkuPatch,
    ) -> SkuResponse:
        """
        Update an existing SKU with the specified parameters.
        Only fields that are explicitly provided in the patch will be updated.
        
        Args:
            sku_id: ID of the SKU to update
            patch: SkuPatch object containing the fields to update
            
        Returns:
            Sku: The updated SKU object
            
        Example:
            >>> from nys_client.skus import SkuPatch, MeasurementUnit
            >>> client.skus.patch(
            ...     sku_id="SKU123",
            ...     patch=SkuPatch(
            ...         name="Updated SKU Name",
            ...         measurement_unit=MeasurementUnit.PIECE
            ...     )
            ... )
        """
        response = self._client._request(
            method="PATCH",
            endpoint=f"api/v2/sku/{sku_id}",
            json=patch.dict(exclude_unset=True)
        )
        
        return SkuResponse(**response.json()) 