import json
from typing import Any
from typing import Self

from grafi.common.decorators.llm_function import llm_function
from grafi.tools.function_calls.function_call_tool import FunctionCallTool
from grafi.tools.function_calls.function_call_tool import FunctionCallToolBuilder


try:
    from duckduckgo_search import DDGS
except ImportError:
    raise ImportError(
        "`duckduckgo-search` not installed. Please install using `pip install duckduckgo-search`"
    )


class DuckDuckGoTool(FunctionCallTool):
    """
    DuckDuckGoTool extends FunctionCallTool to provide web search functionality using the DuckDuckGo Search API.
    """

    # Set up API key and Tavily client
    name: str = "DuckDuckGoTool"
    type: str = "DuckDuckGoTool"
    fixed_max_results: int | None = None
    headers: dict[str, str] | None = None
    proxy: str | None = None
    timeout: int = 10

    @classmethod
    def builder(cls) -> "DuckDuckGoToolBuilder":
        """
        Return a builder for DuckDuckGoTool.
        This method allows for the construction of a DuckDuckGoTool instance with specified parameters.
        """
        return DuckDuckGoToolBuilder(cls)

    @llm_function
    def web_search_using_duckduckgo(self, query: str, max_results: int = 5) -> str:
        """
        Function to search online given a query using the Tavily API. The query can be anything.

        Args:
            query (str): The query to search for.
            max_results (int): The maximum number of results to return (default is 5).

        Returns:
            str: A JSON string containing the search results.
        """
        ddgs = DDGS(
            headers=self.headers,
            proxy=self.proxy,
            timeout=self.timeout,
        )

        return json.dumps(
            ddgs.text(
                keywords=query, max_results=(self.fixed_max_results or max_results)
            ),
            indent=2,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "fixed_max_results": self.fixed_max_results,
            "headers": self.headers,
            "proxy": self.proxy,
            "timeout": self.timeout,
        }

    @classmethod
    async def from_dict(cls, data: dict[str, Any]) -> "DuckDuckGoTool":
        """
        Create a DuckDuckGoTool instance from a dictionary representation.

        Args:
            data (dict[str, Any]): A dictionary representation of the DuckDuckGoTool.

        Returns:
            DuckDuckGoTool: A DuckDuckGoTool instance created from the dictionary.
        """
        from openinference.semconv.trace import OpenInferenceSpanKindValues

        return (
            cls.builder()
            .name(data.get("name", "DuckDuckGoTool"))
            .type(data.get("type", "DuckDuckGoTool"))
            .oi_span_type(OpenInferenceSpanKindValues(data.get("oi_span_type", "TOOL")))
            .fixed_max_results(data.get("fixed_max_results"))
            .headers(data.get("headers"))
            .proxy(data.get("proxy"))
            .timeout(data.get("timeout", 10))
            .build()
        )


class DuckDuckGoToolBuilder(FunctionCallToolBuilder[DuckDuckGoTool]):
    """Builder for DuckDuckGoTool instances."""

    def fixed_max_results(self, fixed_max_results: int) -> Self:
        self.kwargs["fixed_max_results"] = fixed_max_results
        return self

    def headers(self, headers: dict[str, str]) -> Self:
        self.kwargs["headers"] = headers
        return self

    def proxy(self, proxy: str) -> Self:
        self.kwargs["proxy"] = proxy
        return self

    def timeout(self, timeout: int) -> Self:
        self.kwargs["timeout"] = timeout
        return self
