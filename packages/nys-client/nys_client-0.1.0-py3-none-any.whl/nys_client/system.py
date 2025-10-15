from __future__ import annotations
from typing import Any, List
from nys_schemas.system_schema import (
    StorageStatusResponse,
    StorageResponse,
    EnvFileResponse,
    ReportResponse,
    BalconyResponse,
    LevelResponse
)
from .base import BaseResource

class SystemResource(BaseResource[Any]):
    """Resource for interacting with storage-level endpoints."""

    def get_status(self) -> StorageStatusResponse:
        """
        Get the current storage system status.
        Returns:
            The storage status as a StorageStatusResponse object.
        """
        response = self._client._request(
            method="GET",
            endpoint="api/v2/storage_status"
        )
        # The API returns a dict with a 'storage_status' key
        return StorageStatusResponse(**response.json())

    def start(self) -> StorageResponse:
        """
        Start the brain system by calling the /v2/start_brain endpoint.
        Returns the API response as a StorageResponse object.
        """
        response = self._client._request(
            method="POST",
            endpoint="api/v2/start_brain",
        )
        return StorageResponse(**response.json())

    def stop(self) -> StorageResponse:
        """
        Stop the brain system by calling the /v2/stop_brain endpoint.
        Returns the API response as a StorageResponse object.
        """
        response = self._client._request(
            method="POST",
            endpoint="api/v2/stop_brain",
        )
        return StorageResponse(**response.json())
    
    def get_env_file(self) -> EnvFileResponse:
        """
        Get the environment file by calling the /v2/get_env_file endpoint.
        Returns the API response as an EnvFileResponse object.
        """
        response = self._client._request(
            method="GET",
            endpoint="api/v2/get_env_file",
        )
        return EnvFileResponse(**response.json())
    
    def get_report(self) -> ReportResponse:
        """
        Get the report by calling the /v2/get_report endpoint.
        Returns the API response as a ReportResponse object.
        """
        response = self._client._request(
            method="GET",
            endpoint="api/v2/report",
        )
        return ReportResponse(**response.json())
    
    def get_balconies(self) -> List[BalconyResponse]:
        """
        Get the list of balconies by calling the /v2/balconies endpoint.
        Returns the API response as a list of BalconyResponse objects.
        """
        response = self._client._request(
            method="GET",
            endpoint="api/v2/balconies",
        )
        return [BalconyResponse(**balcony) for balcony in response.json()]
    
    def get_levels(self) -> List[LevelResponse]:
        """
        Get the list of levels by calling the /v2/levels endpoint.
        Returns the API response as a list of LevelResponse objects.
        """
        response = self._client._request(
            method="GET",
            endpoint="api/v2/levels",
        )
        return [LevelResponse(**level) for level in response.json()]
    
    def resume_requests(self) -> StorageResponse:
        """
        TODO deprecate
        Resume requests by calling the /v2/resume_requests endpoint.
        Returns the API response as a StorageResponse object.
        """
        response = self._client._request(
            method="POST",
            endpoint="api/v2/resume_requests",
        )
        return StorageResponse(**response.json())
    