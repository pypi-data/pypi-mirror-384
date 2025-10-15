from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Tuple, Literal

from nys_constants.nys_constants import RequestType, RequestStatus, SortOrder
from nys_schemas.request_schema import (
    RequestFilter, 
    RequestSort,
    OnboardingRequestCreateInput,
    OffboardingRequestCreateInput,
    RFIDWriteRequestCreateInput,
    PauseRequestCreateInput,
    ResumeRequestCreateInput,
    FetchRequestCreateInput,
    FulfillmentRequestCreateInput,
    ReplenishmentRequestCreateInput,
    SkuEntityInput,
    CarrierEntityInput,
    RequestResponseComposite,
)

from .base import BaseResource

__all__ = [
    'RequestResource',  # The main resource class
    'RequestFilter',
    'RequestResponseComposite',
    'RequestSort',
    'RequestStatus',
    'RequestType',
    'FetchRequestCreateInput',
    'FulfillmentRequestCreateInput',
    'ReplenishmentRequestCreateInput',
]

class RequestResource(BaseResource[RequestResponseComposite]):
    """Resource for interacting with requests."""

    def create_fetch(
        self,
        entities: List[str],
        priority: Optional[int] = None,
        id: Optional[str] = None,
    ) -> RequestResponseComposite:
        request_input = FetchRequestCreateInput(
                type=RequestType.FETCH,
                priority=priority,
                id=id,
                entities=[CarrierEntityInput(carrier_id=carrier_id) for carrier_id in entities]
            )
        response = self._client._request(
            method="POST",
            endpoint=f"api/v2/requests",
            json=request_input.dict(exclude_unset=True, exclude_none=True)
        )
        return RequestResponseComposite(**response.json())
    
    def create_fulfillment(
        self,
        entities: List[Tuple[str, int]],
        priority: Optional[int] = None,
        id: Optional[str] = None,
    ) -> RequestResponseComposite:
        _entities = [SkuEntityInput(sku_id=sku_id, quantity=quantity) for sku_id, quantity in entities]
        rsp = self._create_fulfillment_or_replenishment_request(RequestType.FULFILLMENT, _entities, priority, id)
        return RequestResponseComposite(**rsp)
    
    def create_replenishment(
        self,
        entities: List[Tuple[str, int]],
        priority: Optional[int] = None,
        id: Optional[str] = None,
    ) -> RequestResponseComposite:
        _entities = [SkuEntityInput(sku_id=sku_id, quantity=quantity) for sku_id, quantity in entities]
        rsp = self._create_fulfillment_or_replenishment_request(RequestType.REPLENISHMENT, _entities, priority, id)
        return RequestResponseComposite(**rsp)
    
    def _create_fulfillment_or_replenishment_request(
        self,
        request_type: Literal[RequestType.FULFILLMENT, RequestType.REPLENISHMENT],
        entities: List[SkuEntityInput],
        priority: Optional[int] = None,
        id: Optional[str] = None,
    ) -> Any:
        assert request_type in [RequestType.FULFILLMENT, RequestType.REPLENISHMENT], f"Invalid request type: {request_type}"

        # Create the request input model
        if request_type == RequestType.FULFILLMENT:
            request_input = FulfillmentRequestCreateInput(
                type=request_type,
                priority=priority,
                id=id,
                entities=entities
            )
        elif request_type == RequestType.REPLENISHMENT:
            request_input = ReplenishmentRequestCreateInput(
                type=request_type,
                priority=priority,
                id=id,
                entities=entities
            )
        else:
            raise ValueError(f"Invalid request type: {request_type}")
        
        # Make the API request
        response = self._client._request(
            method="POST",
            endpoint=f"api/v2/requests",
            json=request_input.dict(exclude_unset=True, exclude_none=True)
        )

        return response.json()

    def search(
        self,
        *,
        filters: Optional[Union[Dict[str, Any], RequestFilter]] = None,
        sort_by: Optional[Union[List[Tuple[RequestSort, SortOrder]], str]] = None,
        page: int = 1,
        size: int = 50
    ) -> List[RequestResponseComposite]:
        """
        Search and filter requests.
        
        Args:
            filters: Request-specific filters. Can be either:
                - A RequestFilter instance with fields like status, type, etc.
                - A dict matching the RequestFilter schema
            sort_by: a list of tuples of (RequestSort, SortOrder) or a string representing the sort order.
                - Example: [(RequestSort.CREATED_AT, SortOrder.DESC)]
                - Example: "-created_at" (for descending order)
            page: Page number (1-based, default: 1)
            size: Items per page (default: 50)
            
        Returns:
            List[RequestResponse]: List of requests matching the filters
            
        Examples:
            Search for executing fulfillment requests using string literals:
            >>> nys_cli.requests.search(
            ...     filters={"status": "EXECUTING", "type": "FULFILLMENT"},
            ...     sort_by="-created_at,
            ... )

            Search using enums (recommended):
            >>> from nys_client.request import RequestType, RequestStatus
            >>> nys_cli.requests.search(
            ...     filters=RequestFilter(status__eq=RequestStatus.EXECUTING, type__eq=RequestType.FULFILLMENT),
            ...     sort_by=[(RequestSort.CREATED_AT, SortOrder.DESC)],
            ... )
        """
        if isinstance(filters, dict):
            filters = RequestFilter(**filters)
            

        return self._search(
            endpoint="api/v2/requests",
            response_model=RequestResponseComposite,
            filters=filters,
            sort_by=sort_by,
            page=page,
            size=size
        )

    def create_onboarding(
        self,
        id: Optional[str] = None,
    ) -> RequestResponseComposite:
        """
        Create a new onboarding request.
        
        Args:
            id: Optional ID (auto-generated if not provided)
            
        Returns:
            RequestResponse containing the created request
            
        Examples:
            >>> nys_cli.requests.create_onboarding()
        """ 
        # Create the request input model
        request_input = OnboardingRequestCreateInput(
            type=RequestType.ONBOARD,
            id=id,
        )
        
        # Make the API request
        response = self._client._request(
            method="POST",
            endpoint="api/v2/requests",
            json=request_input.dict(exclude_unset=True, exclude_none=True)
        )
        # Parse and return the response
        return RequestResponseComposite(**response.json())

    def create_offboarding(
        self,
        bot_id: int,
        id: Optional[str] = None,
    ) -> RequestResponseComposite:
        """
        Create a new offboarding request.
        
        Args:
            bot_id: ID of the bot to offboard
            id: Optional external ID (auto-generated if not provided)
            
        Returns:
            RequestResponse containing the created request
            
        Examples:
            >>> nys_cli.requests.create_offboarding(bot_id=1)
        """
        # Create the request input model
        request_input = OffboardingRequestCreateInput(
            type=RequestType.OFFBOARD,
            id=id,
            bot_id=bot_id,
        )
        
        # Make the API request
        response = self._client._request(
            method="POST",
            endpoint="api/v2/requests",
            json=request_input.dict(exclude_unset=True, exclude_none=True)
        )

        # Parse and return the response
        return RequestResponseComposite(**response.json())

    def create_rfid_write(
        self,
        level_id: int,
        action_type: str,
        start_from_scratch: Optional[bool],
        id: Optional[str] = None,
    ) -> RequestResponseComposite:
        """
        Create a new RFID write request.
        
        Args:
            level_id: ID of the level to write RFID tags on
            action_type: Type of RFID action (e.g., "write", "check", "write_and_check")
            start_from_scratch: Whether to start from scratch (default: True)
            id: Optional ID (auto-generated if not provided)
            
        Returns:
            RequestResponse containing the created request
            
        Examples:
            >>> nys_cli.requests.create_rfid_write(level_id=1, action_type="write")
            >>> nys_cli.requests.create_rfid_write(level_id=2, action_type="check", start_from_scratch=False)
        """
        # Create the request input model
        request_input = RFIDWriteRequestCreateInput(
            type=RequestType.RFID_MAINTENANCE,
            id=id,
            level_id=level_id,
            action_type=action_type,
            start_from_scratch=start_from_scratch
        )
        
        # Make the API request
        response = self._client._request(
            method="POST",
            endpoint="api/v2/requests",
            json=request_input.dict(exclude_unset=True, exclude_none=True)
        )

        # Parse and return the response
        return RequestResponseComposite(**response.json())

    def create_pause(
        self,
        id: Optional[str] = None,
    ) -> RequestResponseComposite:
        """
        Create a new level pause request.
        
        Args:
            id: Optional ID (auto-generated if not provided)
            
        Returns:
            RequestResponse containing the created request
            
        Examples:
            >>> nys_cli.requests.create_pause()
        """
        # Create the request input model
        request_input = PauseRequestCreateInput(
            type=RequestType.PAUSE,
            id=id,
        )
        
        # Make the API request
        response = self._client._request(
            method="POST",
            endpoint="api/v2/requests",
            json=request_input.dict(exclude_unset=True, exclude_none=True)
        )

        # Parse and return the response
        return RequestResponseComposite(**response.json())

    def create_resume(
        self,
        id: Optional[str] =None,
    ) -> RequestResponseComposite:
        """
        Create a new level resume request.
        
        Args:
            priority: Request priority (default: 100)
            id: Optional ID (auto-generated if not provided)
            
        Returns:
            RequestResponse containing the created request
            
        Examples:
            >>> nys_cli.requests.create_resume()
        """
        # Create the request input model
        request_input = ResumeRequestCreateInput(
            type=RequestType.RESUME,
            id=id,
        )
        
        # Make the API request
        response = self._client._request(
            method="POST",
            endpoint="api/v2/requests",
            json=request_input.dict(exclude_unset=True, exclude_none=True)
        )

        # Parse and return the response
        return RequestResponseComposite(**response.json())
    