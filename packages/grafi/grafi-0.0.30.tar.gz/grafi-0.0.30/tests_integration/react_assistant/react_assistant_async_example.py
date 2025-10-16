import asyncio
import os
import uuid

from grafi.common.containers.container import container
from grafi.common.events.topic_events.publish_to_topic_event import PublishToTopicEvent
from grafi.common.models.invoke_context import InvokeContext
from grafi.common.models.message import Message
from grafi.tools.function_calls.impl.tavily_tool import TavilyTool
from tests_integration.react_assistant.react_assistant import ReActAssistant


event_store = container.event_store
tavily_api_key = os.getenv("TAVILY_API_KEY", "")

api_key = os.getenv("OPENAI_API_KEY", "")

observation_llm_system_message = """
You are an AI assistant that records and reports the results obtained from invoked actions.
After performing an action, provide a clear and concise summary of the findings relevant to the user's question.
"""
thought_llm_system_message = """
You are an AI assistant tasked with analyzing the user's question and considering the provided observation to determine the next logical step required to answer the question.
Your response should describe what would be the most effective action to take based on the information gathered.
If the information is sufficient to answer the question, return the answer with confirmation the answer is ready.
"""
action_llm_system_message = """
You are an AI assistant responsible for executing actions based on a given plan to retrieve information.
Specify the appropriate action to take, such as performing a search query or accessing a specific resource, to gather the necessary data.
If answer is ready, return **FINISH REACT**.
"""
summary_llm_system_message = """
You are an AI assistant tasked with summarizing the findings from previous observations to provide a clear and accurate answer to the user's question.
Ensure the summary directly addresses the query based on the information gathered.
"""


def get_invoke_context() -> InvokeContext:
    return InvokeContext(
        conversation_id="conversation_id",
        invoke_id=uuid.uuid4().hex,
        assistant_request_id=uuid.uuid4().hex,
    )


async def test_react_assistant_async() -> None:
    # Set up the assistant with DuckDuckGoTool
    assistant = (
        ReActAssistant.builder()
        .name("ReActAssistant")
        .api_key(api_key)
        .observation_llm_system_message(observation_llm_system_message)
        .thought_llm_system_message(thought_llm_system_message)
        .action_llm_system_message(action_llm_system_message)
        .summary_llm_system_message(summary_llm_system_message)
        .search_tool(
            TavilyTool.builder()
            .name("TavilyTestTool")
            .api_key(tavily_api_key)
            .max_tokens(6000)
            .search_depth("advanced")
            .build()
        )
        .build()
    )

    input_data = [
        Message(
            role="user",
            content="What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?",
        )
    ]

    # Invoke the assistant's function call
    async for output in assistant.invoke(
        PublishToTopicEvent(
            invoke_context=get_invoke_context(),
            data=input_data,
        )
    ):
        print(output)
        assert output is not None

    # Assert that the output is valid and check event count

    print(
        "Number of events recorded:",
        len(await event_store.get_events()),
    )

    # assistant.generate_workflow_graph()
    # assistant.generate_manifest()


asyncio.run(test_react_assistant_async())
