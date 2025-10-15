# NysClient

A Python client library for the Noyes API.

## Installation

```bash
pip install nys-client
```

## Usage

```python
from nys_client import NysClient, RequestType, TriggerStatus

# Initialize client
client = NysClient(api_key="your_api_key")

# Get requests with filtering
requests = client.requests.search(
    filters={"status": "ACCEPTED", "type": "FULFILLMENT"},
    sort_by="-created_at"
)

# Create a new request
new_request = client.requests.create_fulfillment(
    entities=[("SKU123", 1)],
    priority=10
)

# Get jobs with search
jobs = client.jobs.search(
    filters={"status__eq": "EXECUTING", "type__eq": "PICKING"}
)

# Trigger a job
client.jobs.trigger(
    job_id="job-uuid",
    trigger_status=TriggerStatus.SUCCEEDED_TRIGGER
)
```
