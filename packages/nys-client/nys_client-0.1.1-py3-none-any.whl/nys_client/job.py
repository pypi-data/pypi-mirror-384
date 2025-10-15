from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Tuple
from uuid import UUID

from nys_constants.nys_constants import TriggerStatus, JobStatus, JobType, SortOrder
from nys_schemas.job_schema import (
    JobResponse,
    JobFilter,
    JobSort
)

from .base import BaseResource

__all__ = [
    'JobResource',  # The main resource class
    'JobResponse',
    'JobFilter',
    'JobSort',
    'SortOrder',
    'TriggerStatus',
    'JobStatus',
    'JobType',
]

class JobResource(BaseResource[JobResponse]):
    """Resource for interacting with jobs."""

    def search(
        self,
        *,
        filters: Optional[Union[Dict[str, Any], JobFilter]] = None,
        sort_by: Optional[Union[str, List[Tuple[JobSort, SortOrder]]]] = None,
        page: int = 1,
        size: int = 50
    ) -> List[JobResponse]:
        """
        Search and filter jobs.
        
        Args:
            filters: Job-specific filters. Can be either:
                - A JobFilter instance with fields like status__eq, type__eq, etc.
                - A dict matching the JobFilter schema
            sort_by: a list of tuples of (JobSort, SortOrder) or a string representing the sort order.
                - Example: [(JobSort.CREATED_AT, SortOrder.DESC)]
                - Example: "-created_at" (for descending order)
            page: Page number (1-based, default: 1)
            size: Items per page (default: 50)
            
        Returns:
            List[JobResponse]: List of jobs matching the filters
            
        Examples:
            Search using enums (recommended):
            >>> from nys_client.job import JobType, JobStatus, JobSort
            >>> client.jobs.search(
            ...     filters=JobFilter(status__eq=JobStatus.EXECUTING, type__eq=JobType.PICKING),
            ...     sort_by=[(JobSort.CREATED_AT, SortOrder.DESC)]
            ... )

            Search for executing picking jobs using string literals:
            >>> client.jobs.search(
            ...     filters={"status__eq": "EXECUTING", "type__eq": "PICKING"},
            ...     sort_by="-created_at",
            ... )
        """
        if isinstance(filters, dict):
            filters = JobFilter(**filters)

        return self._search(
            endpoint="api/v2/jobs",
            response_model=JobResponse,
            filters=filters,
            sort_by=sort_by,
            page=page,
            size=size
        )

    def trigger(
        self, 
        job_id: Union[str, UUID], 
        trigger_status: TriggerStatus = TriggerStatus.SUCCEEDED_TRIGGER
    ) -> None:
        """
        Trigger a specific job with a status update.
        
        Args:
            job_id: The ID of the job to trigger (string or UUID)
            trigger_status: The trigger status to set (default: SUCCEEDED_TRIGGER)
            
        Raises:
            requests.HTTPError: If the request fails
            
        Example:
            >>> # Trigger a job as succeeded
            >>> nys_cli.jobs.trigger(
            ...     job_id="job-123",
            ...     trigger_status=TriggerStatus.SUCCEEDED_TRIGGER
            ... )
        """
        payload = {
            "trigger_status": trigger_status
        }
        self._client._request(
            method="POST",
            endpoint=f"api/v2/trigger/{job_id}",
            json=payload
        ) 