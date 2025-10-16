# Event Interfaces

## Overview

Graphite uses a consistent event-driven interface pattern where components communicate exclusively through two primary event types:
- **PublishToTopicEvent**: Used to publish data to topics
- **ConsumeFromTopicEvent**: Used to consume data from topics

This design creates a clean separation of concerns and enables loose coupling between components.

## Interface Patterns

### Component Communication Flow

The event interface creates a bidirectional flow pattern:

```mermaid
graph LR
    A[Assistant/Workflow] -->|PublishToTopicEvent| B[Topics]
    B -->|ConsumeFromTopicEvent| C[Nodes]
    C -->|PublishToTopicEvent| D[Topics]
    D -->|ConsumeFromTopicEvent| A
```

### Component Interfaces

| Component | Input Type | Output Type | Description |
|-----------|------------|-------------|-------------|
| **Assistant** | `PublishToTopicEvent` | `List[ConsumeFromTopicEvent]` | Receives published events, returns consumed events |
| **Workflow** | `PublishToTopicEvent` | `List[ConsumeFromTopicEvent]` | Orchestrates nodes through event flow |
| **Node** | `List[ConsumeFromTopicEvent]` | `PublishToTopicEvent` | Consumes events, processes, publishes results |
| **Tool** | `Messages` | `Messages` | Transforms message data (used within nodes) |

## Event Structure

### PublishToTopicEvent

Published when a component sends data to a topic:

```python
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from grafi.models.invoke_context import InvokeContext
from grafi.models.message import Message

event = PublishToTopicEvent(
    publisher_name="ProcessorNode",
    publisher_type="node",
    invoke_context=InvokeContext(session_id="session-123"),
    consumed_event_ids=["evt_1", "evt_2"],  # Events that led to this publication
    data=[Message(role="assistant", content="Processed result")]
)
```

### ConsumeFromTopicEvent

Created when data is consumed from a topic:

```python
from grafi.common.events.topic_events.consume_from_topic_event import ConsumeFromTopicEvent

event = ConsumeFromTopicEvent(
    name="output_topic",
    type=TopicType.DEFAULT_TOPIC_TYPE,
    offset=42,
    publisher_name="ProcessorNode",  # Original publisher
    publisher_type="node",
    invoke_context=InvokeContext(session_id="session-123"),
    consumed_event_ids=["evt_1", "evt_2"],
    data=[Message(role="assistant", content="Processed result")]
)
```

## Implementation Examples

### Assistant Implementation

```python
from grafi.assistants.assistant import Assistant
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from grafi.common.events.topic_events.consume_from_topic_event import ConsumeFromTopicEvent
from typing import List, AsyncGenerator

class MyAssistant(Assistant):
    async def invoke(
        self,
        input_data: PublishToTopicEvent
    ) -> AsyncGenerator[ConsumeFromTopicEvent, None]:
        """Asynchronous streaming of events."""
        async for output in self.workflow.invoke(input_data):
            yield output
```

### Node Implementation

```python
from grafi.nodes.node import Node
from grafi.models.invoke_context import InvokeContext
from grafi.common.events.topic_events.consume_from_topic_event import ConsumeFromTopicEvent
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from typing import List, AsyncGenerator

class ProcessorNode(Node):
    async def invoke(
        self,
        invoke_context: InvokeContext,
        node_input: List[ConsumeFromTopicEvent]
    ) -> AsyncGenerator[PublishToTopicEvent, None]:
        """Process consumed events and publish result."""
        # Execute command on input data
        async for response in self.command.invoke(invoke_context, node_input):
            # Wrap response in PublishToTopicEvent
            yield PublishToTopicEvent(
                publisher_name=self.name,
                publisher_type=self.type,
                invoke_context=invoke_context,
                consumed_event_ids=[event.event_id for event in node_input],
                data=response
            )
```

### Workflow Integration

```python
from grafi.workflows.workflow import Workflow
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from grafi.common.events.topic_events.consume_from_topic_event import ConsumeFromTopicEvent

class MyWorkflow(Workflow):
    async def invoke(self, input_data: PublishToTopicEvent) -> AsyncGenerator[ConsumeFromTopicEvent, None]:
        """Execute workflow asynchronously."""
        # Initialize workflow with input event
        await self.init_workflow(input_data)

        # Process nodes until completion
        while not self._invoke_queue.empty():
            node = self._invoke_queue.get()
            async for output in node.invoke(...):
                # Publish output to topics
                yield output
```

## Benefits of Event Interfaces

### 1. Loose Coupling
Components don't need direct references to each other - they communicate through events and topics.

### 2. Traceability
Every event carries:
- `invoke_context`: Request correlation information
- `consumed_event_ids`: Chain of events that led to this event
- Publisher information: Source component details

### 3. Flexibility
- Easy to add new components without modifying existing ones
- Components can be tested in isolation
- Workflows can be composed dynamically

### 4. Observability
- Complete audit trail through event chain
- Easy to trace data flow through the system
- Built-in support for distributed tracing

### 5. Recovery
- Events can be replayed from any point
- Workflows can resume from interruption
- State can be reconstructed from event history

## Migration from Direct Invocation

If migrating from older patterns that used direct method calls:

**Old Pattern:**
```python
def invoke(self, invoke_context: InvokeContext, input_data: Messages) -> Messages:
    return self.workflow.invoke(invoke_context, input_data)
```

**New Pattern:**
```python
async def invoke(self, input_data: PublishToTopicEvent) -> AsyncGenerator[ConsumeFromTopicEvent, None]:
    async for output in self.workflow.invoke(input_data):
        yield output
```

Key changes:
1. Input is now a single `PublishToTopicEvent` instead of separate context and data
2. Output is an async generator yielding `ConsumeFromTopicEvent` objects
3. Context and data are embedded within the event objects
4. Method is now async and uses `async for` for streaming responses
4. Event IDs enable tracing the full processing chain

## Best Practices

1. **Always preserve event chains**: Include `consumed_event_ids` when creating new events
2. **Use descriptive names**: Set meaningful `publisher_name` values for debugging
3. **Type your components**: Use proper type hints for event interfaces
4. **Handle streaming properly**: Use async generators for streaming responses
5. **Validate event data**: Ensure data types match expected formats

## See Also

- [Events System](./events/events.md) - Detailed event documentation
- [Topics](./topics/topic.md) - Topic-based messaging
- [Event-Driven Workflow](./event-driven-workflow.md) - Workflow orchestration
- [Node](./node.md) - Node component documentation