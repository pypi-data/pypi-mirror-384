# Papa Events

A Python library for event-driven communication between services with a declarative interface.

## Features

- **Declarative Event Handling**: Define event handlers with simple decorators
- **Flexible Event Routing**: Support for exact event names and wildcard patterns
- **Built-in Retry Mechanism**: Automatic retries with configurable limits
- **Dead Letter Queue**: Failed events are moved to DLQ after max retries
- **Failover Support**: Database backup when RabbitMQ is unavailable
- **Pydantic Integration**: Type-safe event payloads with Pydantic models
- **OpenTelemetry Support**: Built-in tracing for event processing

## Installation

```bash
pip install papa-events
```

## Quick Start

### Basic Setup

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from papa_events import PapaApp

# Initialize the event application
event_app = PapaApp(broker_uri="amqp://user:password@localhost/")

@asynccontextmanager
async def lifespan(_: FastAPI):
    await event_app.start()
    yield
    await event_app.stop()

app = FastAPI(lifespan=lifespan)
```

### Event Consumption

Define your event models and handlers:

```python
from pydantic import BaseModel

class UserCreated(BaseModel):
    name: str
    email: str
    age: int

# Handler with event name parameter (optional)
@event_app.on_event(['user.created'], use_case_name="welcome_email")
async def send_welcome_email(event_name: str, event: UserCreated):
    print(f"Processing {event_name} for user: {event.name}")

# Handler without event name parameter
@event_app.on_event(['user.created'], use_case_name="analytics_track")
async def track_user_creation(event: UserCreated):
    print(f"Tracking user: {event.name}")

# Multiple events with wildcards
@event_app.on_event(['user.*', 'company.deleted'], use_case_name="activity_log")
async def log_activity(event_name: str, event: UserCreated):
    print(f"Activity: {event_name} - {event.name}")
```

### Event Publication

#### Publishing Single Events

```python
# From anywhere in your application
user_event = UserCreated(name="John Doe", email="john@example.com", age=30)
await event_app.new_event("user.created", user_event)
```

#### Publishing Events from Handlers

```python
class EmailSent(BaseModel):
    destination: str
    subject: str

@event_app.on_event(['user.created'], use_case_name="send_welcome_email")
async def send_welcome_email(event: UserCreated):
    # Process the event
    print(f"Sending welcome email to {event.email}")
    
    # Return new events to publish
    return [{
        "name": "email.sent",
        "payload": EmailSent(
            destination=event.email,
            subject="Welcome!"
        )
    }]
```

## Advanced Configuration

### Retry Configuration

```python
# Custom retry settings
@event_app.on_event(
    ['user.created'], 
    use_case_name="critical_process",
    retries=10  # Default is 5
)
async def critical_handler(event: UserCreated):
    # Your critical business logic
    pass
```

### Failover Setup

```python
# Initialize with failover database support
event_app = PapaApp(
    broker_uri="amqp://user:password@localhost/",
    failover_uri="postgresql://user:password@localhost/dbname"
)
```

### Advanced Initialization

```python
import logging

# Custom logger and configuration
logger = logging.getLogger("my_events")
event_app = PapaApp(
    broker_uri="amqp://user:password@localhost/",
    max_jobs=50,  # Maximum concurrent event processors
    logger=logger
)
```

## Event Flow

The system creates dedicated queues for each use case. Events are automatically routed to the appropriate queues based on routing keys.

### Processing Flow

1. **Event Received**: Event arrives at the main exchange
2. **Queue Binding**: Event is routed to relevant use case queues
3. **Processing**: Handler processes the event
4. **Success**: Event is acknowledged and removed from queue
5. **Failure**: Event is sent to retry queue with exponential backoff
6. **Max Retries Exceeded**: Event is moved to Dead Letter Queue (DLQ)

### Queue Structure

- `use_case_name`: Main processing queue
- `use_case_name.retry`: Retry queue with delayed delivery
- `use_case_name.dlq`: Dead letter queue for manual intervention

## Error Handling

### Automatic Retries

Events that fail processing are automatically retried with configurable limits. The retry mechanism includes:

- Exponential backoff between retries
- Configurable maximum retry attempts
- Automatic dead letter queue routing after max retries

### Dead Letter Queue

Events that exceed the maximum retry count are moved to the DLQ where they can be:

- Manually inspected
- Reprocessed after fixing the underlying issue
- Archived for audit purposes

## Development

### Running Tests

```bash
# Install development dependencies
uv sync --group dev

# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_events.py -v
```

### Code Quality

```bash
# Format code
uvx ruff format

# Check code style
uvx ruff check

# Type checking
uvx ty check
```

## API Reference

### PapaApp Class

```python
PapaApp(
    broker_uri: str,
    failover_uri: str | None = None,
    max_jobs: int = 20,
    logger: logging.Logger | None = None
)
```

#### Methods

- `on_event(event_names: list[str], use_case_name: str, retries: int = 5)`: Event handler decorator
- `start()`: Initialize connections and start processing
- `stop()`: Gracefully shutdown event processing
- `new_event(event_name: str, payload: bytes | BaseModel)`: Publish new event

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the terms of the LICENSE file included in the distribution.
