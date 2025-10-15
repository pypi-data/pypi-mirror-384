from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime

from nys_constants.nys_constants import RequestType, RequestStatus, JobType, JobStatus, SortOrder
from nys_schemas.requests_and_jobs_view_schema import (
    RequestsAndJobsViewResponse,
    RequestsAndJobsViewFilter,
    RequestsAndJobsViewSort
)

from .base import BaseResource

__all__ = [
    'RequestsAndJobsViewResource',  # The main resource class
    'RequestsAndJobsViewResponse',
    'RequestsAndJobsViewFilter',
    'RequestsAndJobsViewSort',
    'SortOrder',
    'RequestType',
    'RequestStatus',
    'JobType',
    'JobStatus',
]

class RequestsAndJobsViewResource(BaseResource[RequestsAndJobsViewResponse]):
    """Resource for interacting with requests and jobs view."""

    def search(
        self,
        *,
        search: Optional[str] = None,
        filters: Optional[Union[Dict[str, Any], RequestsAndJobsViewFilter]] = None,
        sort_by: Optional[Union[str, List[Tuple[RequestsAndJobsViewSort, SortOrder]]]] = None,
        page: int = 1,
        size: int = 50
    ) -> List[RequestsAndJobsViewResponse]:
        """
        Search and filter requests and jobs from the materialized view.
        
        Args:
            search: search for keywords in the columns
                - Example: "type:PICKING AND status:EXECUTING"
            filters: Request and job specific filters. Can be either:
                - A RequestAndJobsViewFilter instance with fields like status, type, etc.
                - A dict matching the RequestAndJobsViewFilter schema
            sort_by: Field to sort by (from RequestAndJobsViewSort enum)
            page: Page number (1-based, default: 1)
            size: Items per page (default: 50)
            
        Returns:
            List[RequestAndJobsViewResponse]: List of requests and jobs matching the filters
            
        Examples:
            >>> # Using RequestAndJobsViewFilter (recommended)
            >>> from nys_client.requests_and_jobs_view import (
            ...     RequestAndJobsViewFilter,
            ...     RequestAndJobsViewSort,
            ...     JobType,
            ...     JobStatus,
            ...     RequestType,
            ...     RequestStatus
            ... )
            >>> nys_cli.requests_and_jobs_view.search(
            ...     filters=RequestAndJobsViewFilter(
            ...         job_status__eq=JobStatus.EXECUTING,
            ...         job_type__eq=JobType.PICKING,
            ...         request_type__eq=RequestType.FULFILLMENT,
            ...         request_status__eq=RequestStatus.EXECUTING
            ...     ),
            ...     sort_by=[(RequestAndJobsViewSort.CREATED_AT, SortOrder.DESC)]
            ... )

            >>> # Using dictionary with enums
            >>> nys_cli.requests_and_jobs_view.search(
            ...     filters={
            ...         "job_status__in": [JobStatus.EXECUTING, JobStatus.SUCCEEDED],
            ...         "job_type__eq": JobType.PICKING,
            ...         "request_type__eq": RequestType.FULFILLMENT
            ...     },
            ...     sort_by=[(RequestAndJobsViewSort.UPDATED_AT, SortOrder.DESC)]
            ... )
        """
        if isinstance(filters, dict):
            filters = RequestsAndJobsViewFilter(**filters)

        return self._search(
            endpoint="api/v2/requests_and_jobs",
            response_model=RequestsAndJobsViewResponse,
            filters=filters,
            sort_by=sort_by,
            page=page,
            size=size,
            search=search
        ) 