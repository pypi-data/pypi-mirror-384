# NysConstants

Core constants and enums for the Noyes system.

## Installation

```bash
pip install nys_constants
```

## Usage

```python
from nys_constants.nys_constants import (
    RequestType,
    RequestStatus,
    JobType,
    JobStatus,
    TriggerStatus,
    SortOrder,
    EntityType,
    LogLevel,
    OnEmptySKUAction,
    MeasurementUnit,
    StorageModuleType,
    LevelStatus,
    StorageStatus
)

# Use the enums
request_type = RequestType.FULFILLMENT
job_status = JobStatus.EXECUTING
```

## Development

This package is part of the Noyes monorepo. To install in development mode:

```bash
pip install -e .
```






