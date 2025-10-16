from typing import Any
from typing import AsyncGenerator
from typing import Self
from typing import TypeVar

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from grafi.common.containers.container import container
from grafi.common.event_stores.event_store import EventStore
from grafi.common.events.topic_events.consume_from_topic_event import (
    ConsumeFromTopicEvent,
)
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from grafi.common.models.base_builder import BaseBuilder
from grafi.common.models.default_id import default_id
from grafi.workflows.workflow import Workflow


class AssistantBase(BaseModel):
    """
    An abstract base class for assistants that use language models to process input and generate responses.

    Attributes:
        name (str): The name of the assistant
        event_store (EventStore): An instance of EventStore to record events during the assistant's operation.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    assistant_id: str = default_id
    name: str = Field(default="Assistant")
    type: str = Field(default="assistant")
    oi_span_type: OpenInferenceSpanKindValues = Field(
        default=OpenInferenceSpanKindValues.AGENT
    )

    workflow: Workflow = Workflow()

    def model_post_init(self, _context: Any) -> None:
        self._construct_workflow()

    def _construct_workflow(self) -> "AssistantBase":
        """Construct the workflow for the assistant."""
        pass

    async def invoke(
        self, input_data: PublishToTopicEvent, is_sequential: bool = False
    ) -> AsyncGenerator[ConsumeFromTopicEvent, None]:
        """Invoke the assistant's workflow with the provided input data asynchronously."""
        raise NotImplementedError("Subclasses must implement 'invoke'.")

    def to_dict(self) -> dict[str, Any]:
        """Convert the assistant to a dictionary representation."""
        return {
            "assistant_id": self.assistant_id,
            "name": self.name,
            "type": self.type,
            "oi_span_type": self.oi_span_type.value,
            "workflow": self.workflow.to_dict(),
        }

    def stop_workflow(self) -> None:
        """
        Stop the current workflow execution.
        This method allows the assistant to stop an ongoing workflow.
        """
        if hasattr(self.workflow, "stop"):
            self.workflow.stop()
        else:
            # Fallback for workflows that don't support stop method
            logger.warning(
                f"Workflow {self.workflow.__class__.__name__} does not support stop method"
            )

    @classmethod
    async def from_dict(cls, data: dict[str, Any]) -> "AssistantBase":
        """
        Create an Assistant instance from a dictionary representation.

        Args:
            data (dict): A dictionary containing the assistant's attributes.
        Returns:
            Assistant: An instance of the Assistant class.
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("from_dict must be implemented in subclasses.")


T_A = TypeVar("T_A", bound=AssistantBase)


class AssistantBaseBuilder(BaseBuilder[T_A]):
    """Inner builder class for Assistant construction."""

    def oi_span_type(self, oi_span_type: OpenInferenceSpanKindValues) -> Self:
        self.kwargs["oi_span_type"] = oi_span_type
        return self

    def name(self, name: str) -> Self:
        self.kwargs["name"] = name
        return self

    def type(self, type_name: str) -> Self:
        self.kwargs["type"] = type_name
        return self

    def event_store(self, event_store: EventStore) -> Self:
        container.register_event_store(event_store)
        return self
