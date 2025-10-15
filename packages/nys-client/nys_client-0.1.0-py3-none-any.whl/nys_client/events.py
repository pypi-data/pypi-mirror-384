from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Tuple

from nys_constants.nys_constants import SortOrder
from nys_schemas.events_schema import (
    EventsResponse,
    EventsFilter,
    EventsSort,
)

from .base import BaseResource

__all__ = [
    'EventResource',  # The main resource class
    'EventsResponse',
    'EventsFilter',
    'EventsSort',
    'SortOrder',
]

class EventResource(BaseResource[EventsResponse]):
    """Resource for interacting with Events."""

    def search(
        self,
        *,
        search: Optional[str] = None,
        filters: Optional[Union[Dict[str, Any], EventsFilter]] = None,
        sort_by: Optional[Union[str, List[Tuple[EventsSort, SortOrder]]]] = None,
        page: int = 1,
        size: int = 50,
    ) -> List[EventsResponse]:
        """
        Search and filter Events.
        
        Args:
            search: search for keywords in the columns
                - Example: "component:brain OR description:error"
            filters: Event-specific filters. Can be either:
                - A EventsFilter instance with fields like hex_value, component, etc.
                - A dict matching the EventsFilter schema
            sort_by: a list of tuples of (EventsSort, SortOrder) or a string representing the sort order.
                - Example: [(EventsSort.CREATED_AT, SortOrder.DESC)]
                - Example: "-severity" (for descending order)
            page: Page number (1-based, default: 1)
            size: Items per page (default: 50)
            
        Returns:
            List[EventsResponse]: List of Events matching the filters
            
        Examples:
            >>> # Search using a dictionary filter
            >>> client.events.search(
            ...     filters={"component__eq": "brain", "severity__gte": 30}
            ... )
            
            >>> # Search using EventsFilter
            >>> from nys_client.events import EventsFilter, EventsSort, SortOrder
            >>> client.events.search(
            ...     filters=EventsFilter(component__eq="brain"),
            ...     sort_by=[(EventsSort.CREATED_AT, SortOrder.DESC)],
            ...     search="component:brain"
            ... )
            
            >>> # Search with string sort_by
            >>> client.events.search(
            ...     filters=EventsFilter(severity__gte=30),
            ...     sort_by="-created_at,severity",
            ...     search="component:brain"
            ... )
        """
        if isinstance(filters, dict):
            filters = EventsFilter(**filters)

        return self._search(
            endpoint="api/v2/events",
            response_model=EventsResponse,
            filters=filters,
            sort_by=sort_by,
            page=page,
            size=size,
            search=search
        )