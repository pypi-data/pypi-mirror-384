from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Tuple

from nys_constants.nys_constants import OnEmptySKUAction, MeasurementUnit, SortOrder
from nys_schemas.inventory_view_schema import (
    InventoryViewResponse,
    InventoryViewFilter,
    InventoryViewSearch,
    InventoryViewSort,
)

from .base import BaseResource

__all__ = [
    'InventoryViewResource',  # The main resource class
    'InventoryViewResponse',
    'InventoryViewFilter',
    'InventoryViewSort',
    'InventoryViewSearch',
    'SortOrder',
    'OnEmptySKUAction',
    'MeasurementUnit',
]

class InventoryViewResource(BaseResource[InventoryViewResponse]):
    """Resource for interacting with Inventory."""

    def search(
        self,
        *,
        filters: Optional[Union[Dict[str, Any], InventoryViewFilter]] = None,
        search: Optional[str] = None,
        sort_by: Optional[Union[str, List[Tuple[InventoryViewSort, SortOrder]]]] = None,
        page: int = 1,
        size: int = 50
    ) -> List[InventoryViewResponse]:
        """
        Search and filter inventory.
        
        Args:
            filters: Inventory-specific filters. Can be either:
                - An InventoryViewFilter instance with fields like carrier_id, box_id, etc.
                - A dict matching the InventoryViewFilter schema
            search: Search for keywords in fields
                - Example: "carrier_id:123 AND box_id:456"
            sort_by: a list of tuples of (InventoryViewSort, SortOrder) or a string representing the sort order.
                - Example: [(InventoryViewSort.CARRIER_ID, SortOrder.DESC)]
                - Example: "-created_at" (for descending order)
            page: Page number (1-based, default: 1)
            size: Items per page (default: 50)
            
        Returns:
            List[InventoryViewResponse]: List of inventory matching the filters
            
        Examples:
            >>> # Search using InventoryViewFilter (recommended)
            >>> from nys_client.inventory_view import InventoryViewFilter, InventoryViewSort, InventoryViewSearch
            >>> client.inventory_view.search(
            ...     filters=InventoryViewFilter(
            ...         carrier_id__ilike="123",
            ...         box_id__ilike="456"
            ...     ),
            ...     search="carrier_id:123 AND box_id:456",
            ...     sort_by="-created_at",
            ... )

            >>> # Search using a dictionary filter
            >>> from nys_client.inventory_view import InventoryViewSort
            >>> client.inventory_view.search(
            ...     filters={"carrier_id": "123"},
            ...     search="carrier_id:123",
            ...     sort_by=[(InventoryViewSort.CARRIER_ID, SortOrder.DESC)],
            ... )
        """

        if isinstance(filters, dict):
            filters = InventoryViewFilter(**filters)

        if isinstance(sort_by, list):
            assert isinstance(sort_by[0][0], InventoryViewSort), "sort_by must be a list of Tuple[InventoryViewSort, SortOrder]"
            assert isinstance(sort_by[0][1], SortOrder), "sort_by must be a list of Tuple[InventoryViewSort, SortOrder]"
            assert len(sort_by[0]) == 2, "sort_by must be a list of Tuple[InventoryViewSort, SortOrder]"
        

        return self._search(
            endpoint="api/v2/inventory_view",
            response_model=InventoryViewResponse,
            filters=filters,
            search=search,
            sort_by=sort_by,
            page=page,
            size=size
        )

    def delete_load_by_box_id(self, box_id: int):
        """
        Delete a load by its box_id.
        
        Args:
            box_id: The ID of the load to delete
        """
        return self._client._request(
            method='DELETE',
            endpoint=f"api/v2/load/{box_id}",
            params={}
        )
