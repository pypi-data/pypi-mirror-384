# NysClient

A Python client library for the Noyes API.

## Installation

```bash
pip install nys-client
```

## Usage

```python
from nys_client import NysClient, TriggerStatus

# Initialize client
client = NysClient(api_key="your_api_key")

# Get requests with filtering
requests = client.requests.list(
    status="ACCEPTED",
    type="FULFILLMENT",
    sort_by="created_at",
)

# Create a new request
new_request = client.requests.create(
    type="FULFILLMENT",
    priority=10,
    entities=[{
        "entity_type": "SKU",
        "sku_id": "SKU123",
        "quantity": 1
    }]
)

# Get jobs with search
jobs = client.jobs.list(
    quick_search="PICKING",
    status="EXECUTING"
)

# Trigger a job
client.trigger_job(
    job_id="job-uuid",
    trigger_status=TriggerStatus.SUCCEEDED_TRIGGER
)
```

## Development

This package is part of the Noyes monorepo. To install in development mode:

```bash
pip install -e .
```