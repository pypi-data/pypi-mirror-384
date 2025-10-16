# isA Common

Shared Python infrastructure library for the isA platform.

## Overview

This package provides common infrastructure components used across all isA Python services:
- **gRPC Clients**: NATS, MinIO, MQTT, DuckDB, Supabase, etc.
- **Event Framework**: Generic event-driven architecture base classes
- **Proto Files**: Generated gRPC proto files

## Installation

### Development Install (Recommended)

```bash
pip install -e /Users/xenodennis/Documents/Fun/isA_Cloud/isA_common
```

### From Source

```bash
cd /Users/xenodennis/Documents/Fun/isA_Cloud/isA_common
pip install .
```

## Usage

### gRPC Clients

```python
from grpc_clients import NATSClient, MinIOClient, get_client

# Option 1: Direct instantiation
nats = NATSClient(host='localhost', port=50056)

# Option 2: Factory pattern
nats = get_client('nats', user_id='my_service')
```

### Event Framework

```python
from grpc_clients.events import BaseEvent, BaseEventPublisher

# Define your event
class MyEvent(BaseEvent):
    event_type: str = "my.event"
    data: str

# Define your publisher
class MyEventPublisher(BaseEventPublisher):
    def service_name(self) -> str:
        return "my_service"

    async def publish_my_event(self, data: str) -> bool:
        event = MyEvent(event_type="my.event", data=data)
        return await self.publish_event(event, subject="my.event")
```

## Projects Using isA_common

- **isA_user** - Microservices platform (17 services)
- **isA_Model** - AI model inference service
- **isA_Agent** - AI agent service
- **isA_MCP** - Model Control Protocol service

## Components

### gRPC Clients (`grpc_clients/`)

- `NATSClient` - NATS message bus client (port 50056)
- `MinIOClient` - Object storage client (port 50051)
- `MQTTClient` - MQTT broker client (port 50053)
- `DuckDBClient` - Analytics database client (port 50052)
- `SupabaseClient` - Supabase client (port 50057)

### Event Framework (`grpc_clients/events/`)

- `BaseEvent` - Base event model with metadata
- `EventMetadata` - Standard event metadata
- `BaseEventPublisher` - Base publisher class (abstract)
- `BaseEventSubscriber` - Base subscriber class with idempotency
- `EventHandler` - Event handler interface (abstract)
- `IdempotencyChecker` - Duplicate prevention
- `RetryPolicy` - Retry configuration

## Development

### Generating Proto Files

Proto files are generated from the parent `isA_Cloud` project:

```bash
cd /Users/xenodennis/Documents/Fun/isA_Cloud
./scripts/generate-grpc.sh
```

This script generates:
- Go proto files → `api/proto/*.pb.go`
- Python proto files → `isA_common/grpc_clients/proto/*.py`

### Running Tests

```bash
cd /Users/xenodennis/Documents/Fun/isA_Cloud/isA_common
pytest tests/
```

## Package Structure

```
isA_Cloud/
├── isA_common/                      # Python package
│   ├── grpc_clients/
│   │   ├── __init__.py
│   │   ├── base_client.py
│   │   ├── nats_client.py
│   │   ├── minio_client.py
│   │   ├── mqtt_client.py
│   │   ├── duckdb_client.py
│   │   ├── supabase_client.py
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── base_event_models.py
│   │   │   ├── base_event_publisher.py
│   │   │   └── base_event_subscriber.py
│   │   └── proto/
│   │       ├── __init__.py
│   │       ├── common_pb2.py
│   │       ├── nats_service_pb2.py
│   │       └── ...
│   ├── setup.py
│   ├── pyproject.toml
│   ├── README.md
│   └── requirements.txt
├── scripts/
│   └── generate-grpc.sh             # Generates to isA_common/
└── api/proto/                       # Proto definitions
```

## Version

Current version: **0.1.0**

## License

Proprietary - isA Platform
