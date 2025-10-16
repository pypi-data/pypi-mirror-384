# We will test the SimpleLLMAssistant class in this file.

import asyncio
import os
import uuid

from grafi.common.containers.container import container
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from grafi.common.instrumentations.tracing import TracingOptions
from grafi.common.instrumentations.tracing import setup_tracing
from grafi.common.models.async_result import async_func_wrapper
from grafi.common.models.invoke_context import InvokeContext
from grafi.common.models.message import Message
from tests_integration.simple_llm_assistant.simple_llm_assistant import (
    SimpleLLMAssistant,
)


container.register_tracer(setup_tracing(tracing_options=TracingOptions.IN_MEMORY))
event_store = container.event_store

api_key = os.getenv("OPENAI_API_KEY", "")


def get_invoke_context() -> InvokeContext:
    return InvokeContext(
        conversation_id="conversation_id",
        invoke_id=uuid.uuid4().hex,
        assistant_request_id=uuid.uuid4().hex,
    )


async def test_simple_llm_assistant() -> None:
    invoke_context = get_invoke_context()
    assistant = (
        SimpleLLMAssistant.builder()
        .name("SimpleLLMAssistant")
        .system_message(
            """You're a friendly and helpful assistant, always eager to make tasks easier and provide clear, supportive answers.
                You respond warmly to questions, and always call the user's name, making users feel comfortable and understood.
                If you don't have all the information, you reassure users that you're here to help them find the best answer or solution.
                Your tone is approachable and optimistic, and you aim to make each interaction enjoyable."""
        )
        .api_key(api_key)
        .build()
    )
    await event_store.clear_events()

    input_data = [
        Message(content="Hello, my name is Grafi, how are you doing?", role="user")
    ]
    input_data = PublishToTopicEvent(
        invoke_context=invoke_context,
        data=input_data,
    )

    output = await async_func_wrapper(assistant.invoke(input_data, is_sequential=True))
    print(output)
    assert output is not None
    assert len(await event_store.get_events()) == 12

    input_data = [
        Message(
            role="user",
            content="I felt stressful today. Can you help me address my stress by saying my name? It is important to me.",
        )
    ]
    input_data = PublishToTopicEvent(
        invoke_context=get_invoke_context(),
        data=input_data,
    )
    async for output in async_func_wrapper(
        assistant.invoke(input_data, is_sequential=True)
    ):
        print(output)
        assert output is not None
        assert "Grafi" in str(output.data[0].content)
        assert len(await event_store.get_events()) == 24


asyncio.run(test_simple_llm_assistant())
