from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Any
from typing import Dict
from typing import Type
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from grafi.common.models.default_id import default_id
from grafi.common.models.event_id import EventId
from grafi.common.models.invoke_context import InvokeContext


class EventType(Enum):
    NODE_INVOKE = "NodeInvoke"
    NODE_RESPOND = "NodeRespond"
    NODE_FAILED = "NodeFailed"
    TOOL_INVOKE = "ToolInvoke"
    TOOL_RESPOND = "ToolRespond"
    TOOL_FAILED = "ToolFailed"
    WORKFLOW_INVOKE = "WorkflowInvoke"
    WORKFLOW_RESPOND = "WorkflowRespond"
    WORKFLOW_FAILED = "WorkflowFailed"
    ASSISTANT_INVOKE = "AssistantInvoke"
    ASSISTANT_RESPOND = "AssistantRespond"
    ASSISTANT_FAILED = "AssistantFailed"

    TOPIC_EVENT = "TopicEvent"
    PUBLISH_TO_TOPIC = "PublishToTopic"
    CONSUME_FROM_TOPIC = "ConsumeFromTopic"


EVENT_CONTEXT = "event_context"
T_Event = TypeVar("T_Event", bound="Event")


class Event(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    event_id: EventId = default_id
    event_version: str = "1.0"
    invoke_context: InvokeContext
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def event_dict(self) -> Dict[str, Any]:
        # Flatten `invoke_context` fields into the root level
        base_dict = {
            "event_id": self.event_id,
            "event_version": self.event_version,
            "assistant_request_id": self.invoke_context.assistant_request_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
        }
        return base_dict

    @classmethod
    def event_base(cls, event_dict: dict) -> Dict[str, Any]:
        event_id = event_dict["event_id"]
        event_type = EventType(event_dict["event_type"])
        event_version = event_dict["event_version"]
        timestamp = datetime.fromisoformat(event_dict["timestamp"])

        return {
            "event_id": event_id,
            "event_type": event_type,
            "event_version": event_version,
            "timestamp": timestamp,
        }

    def to_dict(self) -> Dict[str, Any]:
        # Return a dictionary representation of the event
        raise NotImplementedError

    @classmethod
    def from_dict(cls: Type[T_Event], data: Dict[str, Any]) -> T_Event:  # generic
        # Return an event object from a dictionary
        raise NotImplementedError
