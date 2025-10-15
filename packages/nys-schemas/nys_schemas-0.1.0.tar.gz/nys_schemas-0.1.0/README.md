# NysSchemas

Shared Pydantic schemas for Noyes packages.

## Installation

```bash
pip install nys_schemas
```

## Usage

```python
from nys_schemas.request_schema import (
    RequestResponseComposite,
    RequestFilter,
    FulfillmentRequestCreateInput
)
from nys_schemas.job_schema import JobResponse, JobFilter
from nys_schemas.bot_schema import Bot, BotResponse

# Use the schemas
request_filter = RequestFilter(status="ACCEPTED")
job_response = JobResponse(id="job-123", status="EXECUTING")
```

## Development

This package is part of the Noyes monorepo. To install in development mode:

```bash
pip install -e .
```