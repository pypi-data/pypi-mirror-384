import json
from unittest.mock import patch

import pytest

from grafi.common.models.invoke_context import InvokeContext
from grafi.common.models.message import Message
from grafi.tools.function_calls.impl.google_search_tool import GoogleSearchTool


# --------------------------------------------------------------------------- #
#  Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def google_search_tool() -> GoogleSearchTool:
    """Default instance with no fixed settings."""
    return GoogleSearchTool.builder().build()


@pytest.fixture
def mock_search():
    """
    Patch the `googlesearch.search` generator so the test never hits the
    real network.  We yield a single fake SearchResult-like object that
    has the same public attrs (title/url/description).
    """
    with patch("grafi.tools.function_calls.impl.google_search_tool.search") as mock:

        class _FakeSearchResult:  # minimal stand-in for googlesearch.SearchResult
            def __init__(self, title, url, desc):
                self.title = title
                self.url = url
                self.description = desc

        mock.return_value = [
            _FakeSearchResult(
                title="Test Title", url="http://example.com", desc="Test Description"
            )
        ]
        yield mock


# --------------------------------------------------------------------------- #
#  Basic initialisation
# --------------------------------------------------------------------------- #
def test_google_search_tool_initialization(google_search_tool: GoogleSearchTool):
    assert google_search_tool.name == "GoogleSearchTool"
    assert google_search_tool.type == "GoogleSearchTool"
    assert google_search_tool.fixed_max_results is None
    assert google_search_tool.timeout == 10


# --------------------------------------------------------------------------- #
#  google_search() helper
# --------------------------------------------------------------------------- #
def test_google_search_function(google_search_tool, mock_search):
    query = "python unit testing"
    max_results = 3
    language = "en"

    result_json = google_search_tool.google_search(
        query=query, max_results=max_results, language=language
    )

    # Make sure the underlying search() function was invoked correctly
    mock_search.assert_called_once_with(
        query,
        num_results=max_results,
        lang=language,
        proxy=None,
        advanced=True,
    )

    assert isinstance(result_json, str)
    parsed = json.loads(result_json)
    assert parsed == [
        {
            "title": "Test Title",
            "url": "http://example.com",
            "description": "Test Description",
        }
    ]


# --------------------------------------------------------------------------- #
#  invoke() dispatcher
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_invoke_function(google_search_tool, mock_search):
    invoke_context = InvokeContext(
        conversation_id="test_conv",
        invoke_id="test_invoke_id",
        assistant_request_id="test_req",
    )
    input_messages = [
        Message(
            role="user",
            content="Search the web",
            tool_calls=[
                {
                    "id": "abc123",
                    "type": "function",
                    "function": {
                        "name": "google_search",
                        "arguments": json.dumps(
                            {"query": "python unit testing", "max_results": 1}
                        ),
                    },
                }
            ],
        )
    ]

    out = []

    async for msg in google_search_tool.invoke(invoke_context, input_messages):
        out.extend(msg)

    assert isinstance(out[0], Message)
    assert out[0].role == "tool"
    assert json.loads(out[0].content) == [
        {
            "title": "Test Title",
            "url": "http://example.com",
            "description": "Test Description",
        }
    ]


# --------------------------------------------------------------------------- #
#  Builder convenience helpers
# --------------------------------------------------------------------------- #
def test_builder_configuration():
    tool = (
        GoogleSearchTool.builder()
        .fixed_max_results(7)
        .proxy("http://proxy.local")
        .timeout(5)
        .build()
    )

    assert tool.fixed_max_results == 7
    assert tool.proxy == "http://proxy.local"
    assert tool.timeout == 5


# --------------------------------------------------------------------------- #
#  Invalid function name
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_invoke_with_invalid_function(google_search_tool):
    invoke_context = InvokeContext(
        conversation_id="test_conv",
        invoke_id="test_invoke_id",
        assistant_request_id="test_req",
    )
    bad_call_message = [
        Message(
            role="user",
            content="Do something",
            tool_calls=[
                {
                    "id": "bad",
                    "type": "function",
                    "function": {"name": "non_existent", "arguments": "{}"},
                }
            ],
        )
    ]

    result = []
    async for msg in google_search_tool.invoke(invoke_context, bad_call_message):
        result.extend(msg)
    assert result == []


# --------------------------------------------------------------------------- #
#  Error path
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_error_handling(google_search_tool):
    with patch("grafi.tools.function_calls.impl.google_search_tool.search") as mock:
        mock.side_effect = Exception("Search failed")

        invoke_context = InvokeContext(
            conversation_id="test_conv",
            invoke_id="test_invoke_id",
            assistant_request_id="test_req",
        )
        message_with_call = [
            Message(
                role="user",
                content="Search for errors",
                tool_calls=[
                    {
                        "id": "err",
                        "type": "function",
                        "function": {
                            "name": "google_search",
                            "arguments": '{"query": "Python"}',
                        },
                    }
                ],
            )
        ]

        from grafi.common.exceptions import FunctionCallException

        with pytest.raises(FunctionCallException) as excinfo:
            async for msg in google_search_tool.invoke(
                invoke_context, message_with_call
            ):
                assert msg  # should not reach here
        assert "Search failed" in str(excinfo.value)


# --------------------------------------------------------------------------- #
#  from_dict
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_from_dict():
    """Test deserialization from dictionary."""
    data = {
        "class": "GoogleSearchTool",
        "tool_id": "test-id",
        "name": "TestGoogleSearch",
        "type": "GoogleSearchTool",
        "oi_span_type": "TOOL",
        "fixed_max_results": 5,
        "fixed_language": "en",
        "headers": {"User-Agent": "test"},
        "proxy": "http://proxy.test",
        "timeout": 15,
    }

    tool = await GoogleSearchTool.from_dict(data)

    assert isinstance(tool, GoogleSearchTool)
    assert tool.name == "TestGoogleSearch"
    assert tool.fixed_max_results == 5
    assert tool.fixed_language == "en"
    assert tool.headers == {"User-Agent": "test"}
    assert tool.proxy == "http://proxy.test"
    assert tool.timeout == 15


@pytest.mark.asyncio
async def test_from_dict_roundtrip():
    """Test that serialization and deserialization are consistent."""
    original = (
        GoogleSearchTool.builder()
        .name("TestGoogle")
        .fixed_max_results(3)
        .fixed_language("en")
        .headers({"User-Agent": "test"})
        .build()
    )

    # Serialize to dict
    data = original.to_dict()

    # Deserialize back
    restored = await GoogleSearchTool.from_dict(data)

    # Verify key properties match
    assert restored.name == original.name
    assert restored.fixed_max_results == original.fixed_max_results
    assert restored.fixed_language == original.fixed_language
    assert restored.headers == original.headers
