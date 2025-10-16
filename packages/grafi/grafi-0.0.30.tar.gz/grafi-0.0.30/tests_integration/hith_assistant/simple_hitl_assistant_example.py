import asyncio
import json
import os
import uuid

from grafi.common.containers.container import container
from grafi.common.decorators.llm_function import llm_function
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from grafi.common.models.async_result import async_func_wrapper
from grafi.common.models.invoke_context import InvokeContext
from grafi.common.models.message import Message
from grafi.tools.function_calls.function_call_tool import FunctionCallTool
from tests_integration.hith_assistant.simple_hitl_assistant import SimpleHITLAssistant


event_store = container.event_store

api_key = os.getenv("OPENAI_API_KEY", "")


class HumanInfo(FunctionCallTool):
    @llm_function
    def request_human_information(self, question_description: str) -> str:
        """
        Requests human input for personal information based on a given question description.
        This method simulates requesting information from a human user during test scenarios.
        It prompts the user with a specific question about personal information based on the
        provided context.

        Args:
            question_description (str): The question or prompt to ask the human user for personal information.

        Returns:
            dict: An dictionary representing a questionary schema for the user to fill out.
        """
        return json.dumps(
            {
                "question_description": question_description,
                "name": "string",
            }
        )


assistant_request_id = uuid.uuid4().hex


def get_invoke_context() -> InvokeContext:
    return InvokeContext(
        conversation_id="conversation_id",
        invoke_id=uuid.uuid4().hex,
        assistant_request_id=assistant_request_id,
    )


async def test_simple_hitl_assistant() -> None:
    assistant = (
        SimpleHITLAssistant.builder()
        .name("SimpleHITLAssistant")
        .api_key(api_key)
        .hitl_llm_system_message(
            "You are an AI assistant analysis the request, if request required user then ask user to provide information."
        )
        .summary_llm_system_message(
            "You are an AI assistant tasked with summarizing the findings from previous observations to provide a clear and accurate answer to the user's question. Ensure the summary directly addresses the query based on the information gathered."
        )
        .hitl_request(HumanInfo(name="request_human_information"))
        .build()
    )

    # Test the run method
    input_data = [
        Message(
            role="user",
            content="Hello, I want to register the gym. This gym require user's name and user's age separately. Can you help me?",
        )
    ]

    input_data = PublishToTopicEvent(
        invoke_context=get_invoke_context(),
        data=input_data,
    )

    output = await async_func_wrapper(assistant.invoke(input_data, is_sequential=True))

    print(output)

    events = await event_store.get_events()
    print(len(events))
    assert len(events) == 18

    human_input = [
        Message(
            role="user",
            content="My name is craig.",
        )
    ]

    input_data = PublishToTopicEvent(
        invoke_context=get_invoke_context(),
        data=human_input,
        consumed_event_ids=[event.event_id for event in output],
    )

    output = await async_func_wrapper(assistant.invoke(input_data, is_sequential=True))

    events = await event_store.get_events()
    print(len(events))
    assert len(events) == 36

    human_input = [
        Message(
            role="user",
            content="My age is 30.",
        )
    ]

    input_data = PublishToTopicEvent(
        invoke_context=get_invoke_context(),
        data=human_input,
        consumed_event_ids=[event.event_id for event in output],
    )

    output = await async_func_wrapper(assistant.invoke(input_data, is_sequential=True))

    print(output)

    events = await event_store.get_events()
    print(len(events))
    assert len(events) == 54


asyncio.run(test_simple_hitl_assistant())
