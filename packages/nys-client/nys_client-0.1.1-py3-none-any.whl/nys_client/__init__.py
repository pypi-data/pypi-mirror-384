"""
A Python client library for the Noyes API.
            
        Example:
    >>> from nys_client import NysClient, RequestType, TriggerStatus
    >>> 
    >>> # Initialize client
    >>> client = NysClient(api_key="your_api_key")
    >>> 
    >>> # Create a request
    >>> new_request = client.requests.create( #TODO
            ...     request_type=RequestType.FULFILLMENT,
    ...     entities=[("123", 1)]
    ... )
    >>> 
    >>> # Search for jobs
    >>> jobs = client.jobs.search(
    ...     filters={"status": "EXECUTING", "type": "PICKING"}
    ... )
    >>> 
    >>> # Trigger a job
    >>> client.jobs.trigger(
    ...     job_id="job-123",
    ...     trigger_status=TriggerStatus.SUCCEEDED_TRIGGER
            ... )
        """

from .client import NysClient
from .system import SystemResource
from .bot import BotResource

# Re-export commonly used types from nys_schemas and nys_constants
from nys_constants.nys_constants import (
    RequestType,
    RequestStatus,
    JobType,
    JobStatus,
    TriggerStatus,
    SortOrder,
)

from nys_schemas.request_schema import (
    RequestResponseComposite,
    RequestFilter,
    FulfillmentRequestCreateInput,
    FetchRequestCreateInput,
    ReplenishmentRequestCreateInput,
    OnboardingRequestCreateInput,
    OffboardingRequestCreateInput,
    RFIDWriteRequestCreateInput,
    PauseRequestCreateInput,
    ResumeRequestCreateInput,
)
from nys_schemas.job_schema import (
    JobResponse,
    JobFilter,
)
from nys_schemas.bot_schema import (
    Bot,
    BotResponse,
    BotChargingRequest,
    BotChargingResponse,
    BotStopChargingRequest,
    BotStopChargingResponse,
    BotRemoveResponse,
)
from nys_schemas.load_schema import (
    LoadResponse,
    LoadCreate,
    LoadPatch,
)

__all__ = [
    # Main client class
    'NysClient',
    
    # Response models - Core entities
    'RequestResponseComposite',
    'JobResponse',
    'BotResponse',
    
    # Request/Input models
    'RequestCreateInputGeneric',
    'RequestFilter',
    'JobFilter',
    'BotChargingRequest',
    'BotChargingResponse',
    'BotStopChargingRequest', 
    'BotStopChargingResponse',
    'BotRemoveResponse',
    'Bot',
    'FetchRequestCreateInput',
    'FulfillmentRequestCreateInput',
    'ReplenishmentRequestCreateInput',
    'OnboardingRequestCreateInput',
    'OffboardingRequestCreateInput',
    'RFIDWriteRequestCreateInput',
    'PauseRequestCreateInput',
    'ResumeRequestCreateInput',
    
    # Load models
    'LoadResponse',
    'LoadCreate',
    'LoadPatch',

    
    # Enums and Constants
    'RequestType',
    'RequestStatus',
    'JobType',
    'JobStatus',
    'TriggerStatus',
    'SortOrder',
] 

__version__ = "0.1.0"