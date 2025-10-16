import os
from typing import Optional
from typing import Self

from openinference.semconv.trace import OpenInferenceSpanKindValues
from pydantic import Field

from grafi.assistants.assistant import Assistant
from grafi.assistants.assistant_base import AssistantBaseBuilder
from grafi.nodes.node import Node
from grafi.tools.function_calls.function_call_tool import FunctionCallTool
from grafi.tools.llms.impl.openai_tool import OpenAITool
from grafi.topics.expressions.subscription_builder import SubscriptionBuilder
from grafi.topics.topic_impl.input_topic import InputTopic
from grafi.topics.topic_impl.output_topic import OutputTopic
from grafi.topics.topic_impl.topic import Topic
from grafi.workflows.impl.event_driven_workflow import EventDrivenWorkflow


class SimpleFunctionCallAssistant(Assistant):
    """
    A simple assistant class that uses OpenAI's language model to process input,
    make function calls, and generate responses.

    This class sets up a workflow with three nodes: an input LLM node, a function call node,
    and an output LLM node. It provides a method to run input through this workflow.

    Attributes:
        name (str): The name of the assistant.
        api_key (str): The API key for OpenAI. If not provided, it tries to use the OPENAI_API_KEY environment variable.
        model (str): The name of the OpenAI model to use.
        event_store (EventStore): An instance of EventStore to record events during the assistant's operation.
        function (Callable): The function to be called by the assistant.
    """

    oi_span_type: OpenInferenceSpanKindValues = Field(
        default=OpenInferenceSpanKindValues.AGENT
    )
    name: str = Field(default="SimpleFunctionCallAssistant")
    type: str = Field(default="SimpleFunctionCallAssistant")
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    model: str = Field(default="gpt-4o-mini")
    function_call_llm_system_message: Optional[str] = Field(default=None)
    summary_llm_system_message: Optional[str] = Field(default=None)
    function_tool: FunctionCallTool

    @classmethod
    def builder(cls) -> "SimpleFunctionCallAssistantBuilder":
        """Return a builder for SimpleFunctionCallAssistant."""
        return SimpleFunctionCallAssistantBuilder(cls)

    def _construct_workflow(self) -> "SimpleFunctionCallAssistant":
        agent_input_topic = InputTopic(name="agent_input_topic")
        agent_output_topic = OutputTopic(name="agent_output_topic")
        function_call_topic = Topic(
            name="function_call_topic",
            condition=lambda event: event.data[-1].tool_calls
            is not None,  # only when the last message is a function call
        )

        llm_input_node = (
            Node.builder()
            .name("OpenAIInputNode")
            .type("LLMNode")
            .subscribe(SubscriptionBuilder().subscribed_to(agent_input_topic).build())
            .tool(
                OpenAITool.builder()
                .name("UserInputLLM")
                .api_key(self.api_key)
                .model(self.model)
                .system_message(self.function_call_llm_system_message)
                .build()
            )
            .publish_to(function_call_topic)
            .publish_to(agent_output_topic)
            .build()
        )

        # Create a function call node

        function_result_topic = Topic(name="function_result_topic")

        agent_output_topic.condition = (
            lambda event: event.data[-1].content is not None
            and isinstance(event.data[-1].content, str)
            and event.data[-1].content.strip() != ""
        )

        function_call_node = (
            Node.builder()
            .name("FunctionCallNode")
            .type("FunctionCallNode")
            .subscribe(SubscriptionBuilder().subscribed_to(function_call_topic).build())
            .tool(self.function_tool)
            .publish_to(function_result_topic)
            .build()
        )

        # Create an output LLM node
        llm_output_node = (
            Node.builder()
            .name("OpenAIOutputNode")
            .type("LLMNode")
            .subscribe(
                SubscriptionBuilder().subscribed_to(function_result_topic).build()
            )
            .tool(
                OpenAITool.builder()
                .name("UserOutputLLM")
                .api_key(self.api_key)
                .model(self.model)
                .system_message(self.summary_llm_system_message)
                .build()
            )
            .publish_to(agent_output_topic)
            .build()
        )

        # Create a workflow and add the nodes
        self.workflow = (
            EventDrivenWorkflow.builder()
            .name("simple_function_call_workflow")
            .node(llm_input_node)
            .node(function_call_node)
            .node(llm_output_node)
            .build()
        )

        return self


class SimpleFunctionCallAssistantBuilder(
    AssistantBaseBuilder[SimpleFunctionCallAssistant]
):
    """
    Concrete builder for SimpleFunctionCallAssistant.
    This builder allows setting the API key, model, system messages, and function tool.
    """

    def api_key(self, api_key: str) -> Self:
        self.kwargs["api_key"] = api_key
        return self

    def model(self, model: str) -> Self:
        self.kwargs["model"] = model
        return self

    def function_call_llm_system_message(
        self, function_call_llm_system_message: str
    ) -> Self:
        self.kwargs[
            "function_call_llm_system_message"
        ] = function_call_llm_system_message
        return self

    def summary_llm_system_message(self, summary_llm_system_message: str) -> Self:
        self.kwargs["summary_llm_system_message"] = summary_llm_system_message
        return self

    def function_tool(self, function_tool: FunctionCallTool) -> Self:
        self.kwargs["function_tool"] = function_tool
        return self
