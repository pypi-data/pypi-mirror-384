from __future__ import annotations

from nys_schemas.load_schema import (
    LoadResponse,
    LoadCreate,
    LoadPatch,
)

from .base import BaseResource

__all__ = [
    'LoadResource',  # The main resource class
    'LoadResponse',
    'LoadCreate',
    'LoadPatch',
]

class LoadResource(BaseResource[LoadResponse]):
    """Resource for interacting with loads."""

    def create(
        self,
        box_id: int,
        load: LoadCreate
    ) -> LoadResponse:
        """
        Create a new load for a specific box.
        
        Args:
            box_id: ID of the box to create the load for
            load: LoadCreate object containing the load parameters
            
        Returns:
            LoadResponse: The created load object
            
        Example:
            >>> nys_cli.loads.create(
            ...     box_id=123,
            ...     load=LoadCreate(
            ...         sku_id="SKU123",
            ...         item_count=10,
            ...         item_count_max=20
            ...     )
            ... )
        """
        response = self._client._request(
            method="POST",
            endpoint=f"api/v2/load/{box_id}",
            json=load.dict(exclude_unset=True)
        )
        
        return LoadResponse(**response.json())

    def patch(
        self,
        box_id: int,
        patch: LoadPatch,
    ) -> LoadResponse:
        """
        Update an existing load for a specific box.
        Only fields that are explicitly provided in the patch will be updated.
        
        Args:
            box_id: ID of the box whose load to update
            patch: LoadPatch object containing the fields to update
            
        Returns:
            LoadResponse: The updated load object
            
        Example:
            >>> nys_cli.loads.patch(
            ...     box_id=123,
            ...     patch=LoadPatch(
            ...         sku_id="SKU456",
            ...         item_count=15,
            ...         item_count_max=25
            ...     )
            ... )
        """
        response = self._client._request(
            method="PATCH",
            endpoint=f"api/v2/load/{box_id}",
            json=patch.dict(exclude_unset=True)
        )
        
        return LoadResponse(**response.json())

    def delete(
        self,
        box_id: int,
    ) -> None:
        """
        Delete a load for a specific box.
        
        Args:
            box_id: ID of the box whose load to delete
            
        Example:
            >>> nys_cli.loads.delete(box_id=123)
        """
        response =self._client._request(
            method="DELETE",
            endpoint=f"api/v2/load/{box_id}"
        ) 
        return response