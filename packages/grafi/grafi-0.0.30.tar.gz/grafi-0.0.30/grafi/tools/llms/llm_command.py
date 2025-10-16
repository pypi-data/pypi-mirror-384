from typing import List

from loguru import logger

from grafi.common.containers.container import container
from grafi.common.events.component_events import AssistantRespondEvent
from grafi.common.events.event_graph import EventGraph
from grafi.common.events.topic_events.consume_from_topic_event import (
    ConsumeFromTopicEvent,
)
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from grafi.common.models.invoke_context import InvokeContext
from grafi.common.models.message import Message
from grafi.common.models.message import Messages
from grafi.tools.command import Command


class LLMCommand(Command):
    async def get_tool_input(
        self,
        invoke_context: InvokeContext,
        node_input: List[ConsumeFromTopicEvent],
    ) -> Messages:
        """Prepare the input for the LLM command based on the node input and invoke context."""

        # Get conversation history messages from the event store

        conversation_events = await container.event_store.get_conversation_events(
            invoke_context.conversation_id
        )

        assistant_respond_event_dict = {
            event.event_id: event
            for event in conversation_events
            if isinstance(event, AssistantRespondEvent)
        }

        # Get all the input and output message from assistant respond events as list
        all_messages: Messages = []
        for event in assistant_respond_event_dict.values():
            if (
                event.invoke_context.assistant_request_id
                != invoke_context.assistant_request_id
            ):
                all_messages.extend(event.input_data.data)
                for output_event in event.output_data:
                    all_messages.extend(output_event.data)

        # Retrieve agent events related to the current assistant request
        agent_events = await container.event_store.get_agent_events(
            invoke_context.assistant_request_id
        )
        topic_events = {
            event.event_id: event
            for event in agent_events
            if isinstance(event, ConsumeFromTopicEvent)
            or isinstance(event, PublishToTopicEvent)
        }
        event_graph = EventGraph()
        event_graph.build_graph(node_input, topic_events)

        node_input_datas = [
            event_node.event for event_node in event_graph.get_topology_sorted_events()
        ]

        all_messages.extend([msg for event in node_input_datas for msg in event.data])

        # Make sure the llm tool call message are followed by the function call messages
        # Step 1: get all the messages with tool_call_id and remove them from the messages list
        tool_call_messages = {
            msg.tool_call_id: msg
            for msg in all_messages
            if msg.tool_call_id is not None
        }
        all_messages = [msg for msg in all_messages if msg.tool_call_id is None]

        sorted_messages: Messages = sorted(
            all_messages, key=lambda item: item.timestamp
        )

        # Step 2: loop over the messages again, find the llm messages with tool_calls, and append corresponding the tool_call_messages
        i = 0
        while i < len(sorted_messages):
            message = sorted_messages[i]
            if message.tool_calls is not None:
                for tool_call in message.tool_calls:
                    if tool_call.id in tool_call_messages:
                        sorted_messages.insert(i + 1, tool_call_messages[tool_call.id])
                    else:
                        logger.warning(
                            f"Tool call message not found for id: {tool_call.id}, add an empty message"
                        )
                        message_args = {
                            "role": "tool",
                            "content": None,
                            "tool_call_id": tool_call.id,
                        }
                        sorted_messages.insert(
                            i + 1, Message.model_validate(message_args)
                        )
                i += len(message.tool_calls) + 1
            else:
                i += 1

        return sorted_messages
