from __future__ import annotations
import logging
import requests
from typing import Optional

from .request import RequestResource
from .job import JobResource
from .skus import SkuResource
from .loads import LoadResource
from .requests_and_jobs_view import RequestsAndJobsViewResource
from .inventory_view import InventoryViewResource
from .system import SystemResource
from .bot import BotResource
from .events import EventResource
logger = logging.getLogger(__name__)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class NysClient:
    """Client for interacting with the Noyes API."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://noyes-api:8003",
        # TODO: Increased timeout to 60 seconds for long-running requests. Eg. stop_brain endpoint
        timeout: int = 60 # seconds
    ):
        """
        Initialize the NysClient.
        
        Args:
            api_key: Your API key
            base_url: Base URL of the API (default: http://noyes-api:8003)
            timeout: Request timeout in seconds (default: 60)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Initialize resources
        self._requests = RequestResource(self)
        self._jobs = JobResource(self)
        self._skus = SkuResource(self)
        self._loads = LoadResource(self)
        self._requests_and_jobs_view = RequestsAndJobsViewResource(self)
        self._inventory_view = InventoryViewResource(self)
        self._system = SystemResource(self)
        self._bots = BotResource(self)
        self._events = EventResource(self)
    
    @property
    def requests(self) -> RequestResource:
        """Access request-related operations."""
        return self._requests
    
    @property
    def jobs(self) -> JobResource:
        """Access job-related operations."""
        return self._jobs

    @property
    def skus(self) -> SkuResource:
        """Access SKU-related operations."""
        return self._skus

    @property
    def loads(self) -> LoadResource:
        """Access load-related operations."""
        return self._loads

    @property
    def requests_and_jobs_view(self) -> RequestsAndJobsViewResource:
        """Access requests and jobs view operations."""
        return self._requests_and_jobs_view

    @property
    def inventory_view(self) -> InventoryViewResource:
        """Access inventory view operations."""
        return self._inventory_view

    @property
    def system(self) -> SystemResource:
        """Access system-related operations."""
        return self._system
        
    @property
    def bots(self) -> BotResource:
        """Access bot-related operations."""
        return self._bots

    @property
    def events(self) -> EventResource:
        """Access event-related operations."""
        return self._events

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make a request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            json: JSON body
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            requests.Response: Response from the API
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json,
            timeout=self.timeout,
            headers=self._headers,
            **kwargs
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            logger.error(f"Response content: {response.text}")
            raise e
        return response