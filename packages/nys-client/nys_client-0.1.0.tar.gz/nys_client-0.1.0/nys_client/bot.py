from __future__ import annotations
from typing import Any, Dict, List, Optional
from nys_schemas.bot_schema import (
    Bot,
    BotResponse,
    BotFilter,
    BotSort,
    BotChargingRequest,
    BotChargingResponse,
    BotStopChargingRequest,
    BotStopChargingResponse,
    BotRemoveResponse
)
from .base import BaseResource

__all__ = [
    'BotResource',  # The main resource class
    'Bot',
    'BotResponse',
    'BotFilter',
    'BotSort',
    'BotChargingRequest',
    'BotChargingResponse',
    'BotStopChargingRequest',
    'BotStopChargingResponse',
    'BotRemoveResponse'
]

class BotResource(BaseResource[BotResponse]):
    """Resource for interacting with Bots."""

    def get_bots(self) -> List[BotResponse]:
        """
        Get all bots.
        
        Returns:
            List[BotResponse]: List of all bots in the system
            
        Examples:
            >>> bots = client.bots.get_bots()
            >>> for bot in bots:
            ...     print(f"Bot ID: {bot.idx}, Level: {bot.level_id}, Battery: {bot.battery_level}%")
        """
        response = self._client._request(
            method="GET",
            endpoint="api/v2/bots"
        )
        return [BotResponse(**item) for item in response.json()]

    def go_charging(self, charging_request: BotChargingRequest) -> BotChargingResponse:
        """
        Send specified bots to charging stations.
        
        This endpoint proxies the request to the brain API which handles the ROS communication.
        
        Args:
            charging_request: The request parameters including bot_idxs, force flag, 
                             block_until_done flag, and timeout
                             
        Returns:
            BotChargingResponse: Response with success/failure information
            
        Examples:
            >>> from nys_client.bot import BotChargingRequest
            >>> response = client.bots.go_charging(
            ...     BotChargingRequest(
            ...         bot_ids=["1", "2"],
            ...         force=True,
            ...         block_until_done=False,
            ...         timeout=180
            ...     )
            ... )
            >>> print(f"Success: {response.success}, Message: {response.message}")
        """
        response = self._client._request(
            method="POST",
            endpoint="api/v2/bot/go_charging",
            json=charging_request.dict()
        )
        return BotChargingResponse(**response.json())

    def stop_charging(self, stop_charging_request: BotStopChargingRequest) -> BotStopChargingResponse:
        """
        Stop charging for specified bots.
        
        This endpoint proxies the request to the brain API which handles the ROS communication.
        
        Args:
            stop_charging_request: The request parameters including bot_idxs and force flag
            
        Returns:
            BotStopChargingResponse: Response with success/failure information
            
        Examples:
            >>> from nys_client.bot import BotStopChargingRequest
            >>> response = client.bots.stop_charging(
            ...     BotStopChargingRequest(
            ...         bot_ids=["1", "2"],
            ...         force=True
            ...     )
            ... )
            >>> print(f"Success: {response.success}, Message: {response.message}")
        """
        response = self._client._request(
            method="POST",
            endpoint="api/v2/bot/stop_charging",
            json=stop_charging_request.dict()
        )
        return BotStopChargingResponse(**response.json())

    def remove_bots(self, bot_ids: List[str]) -> BotRemoveResponse:
        """
        Remove specified bots from the database.
        
        Warning: This is not the usual offboarding process. Use at your own risk!
        
        Args:
            bot_ids: List of bot IDs to remove from database; use ["*"] for all bots
            
        Returns:
            BotRemoveResponse: Response with success/failure information
            
        Examples:
            >>> response = client.bots.remove_bots(["1", "2"])
            >>> print(f"Success: {response.success}, Message: {response.message}")
        """
        response = self._client._request(
            method="DELETE",
            endpoint="api/v2/bot",
            params={"bot_ids": bot_ids}
        )
        return BotRemoveResponse(**response.json())