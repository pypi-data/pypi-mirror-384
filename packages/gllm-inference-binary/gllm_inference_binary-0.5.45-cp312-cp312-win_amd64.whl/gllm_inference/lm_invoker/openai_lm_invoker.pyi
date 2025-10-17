from _typeshed import Incomplete
from gllm_core.event import EventEmitter as EventEmitter
from gllm_core.schema.tool import Tool as Tool
from gllm_core.utils.retry import RetryConfig as RetryConfig
from gllm_inference.constants import INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES, OPENAI_DEFAULT_URL as OPENAI_DEFAULT_URL
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.lm_invoker.schema.openai import InputType as InputType, Key as Key, OutputType as OutputType, ReasoningEffort as ReasoningEffort, ReasoningSummary as ReasoningSummary
from gllm_inference.schema import ActivityEvent as ActivityEvent, Attachment as Attachment, AttachmentType as AttachmentType, CodeEvent as CodeEvent, CodeExecResult as CodeExecResult, LMOutput as LMOutput, MCPCall as MCPCall, MCPCallActivity as MCPCallActivity, MCPListToolsActivity as MCPListToolsActivity, MCPServer as MCPServer, Message as Message, MessageRole as MessageRole, ModelId as ModelId, ModelProvider as ModelProvider, Reasoning as Reasoning, ResponseSchema as ResponseSchema, ThinkingEvent as ThinkingEvent, TokenUsage as TokenUsage, ToolCall as ToolCall, ToolResult as ToolResult, WebSearchActivity as WebSearchActivity
from gllm_inference.utils import validate_string_enum as validate_string_enum
from langchain_core.tools import Tool as LangChainTool
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
STREAM_DATA_START_TYPE_MAP: Incomplete
STREAM_DATA_END_TYPE_MAP: Incomplete
STREAM_DATA_CONTENT_TYPE_MAP: Incomplete

class OpenAILMInvoker(BaseLMInvoker):
    '''A language model invoker to interact with OpenAI language models.

    This class provides support for OpenAI\'s Responses API schema, which is recommended by OpenAI as the preferred API
    to use whenever possible. Use this class unless you have a specific reason to use the Chat Completions API instead.
    The Chat Completions API schema is supported through the `OpenAIChatCompletionsLMInvoker` class.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        client_kwargs (dict[str, Any]): The keyword arguments for the OpenAI client.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Tool]): The list of tools provided to the model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig): The retry configuration for the language model.
        reasoning_effort (ReasoningEffort | None): The reasoning effort for reasoning models. Not allowed
            for non-reasoning models. If None, the model will perform medium reasoning effort.
        reasoning_summary (ReasoningSummary | None): The reasoning summary level for reasoning models. Not allowed
            for non-reasoning models. If None, no summary will be generated.
        mcp_servers (list[MCPServer]): The list of MCP servers to enable MCP tool calling.
        code_interpreter (bool): Whether to enable the code interpreter.
        web_search (bool): Whether to enable the web search.

    Basic usage:
        The `OpenAILMInvoker` can be used as follows:
        ```python
        lm_invoker = OpenAILMInvoker(model_name="gpt-5-nano")
        result = await lm_invoker.invoke("Hi there!")
        ```

    OpenAI compatible endpoints:
        The `OpenAILMInvoker` can also be used to interact with endpoints that are compatible with
        OpenAI\'s Responses API schema. This includes but are not limited to:
        1. SGLang (https://github.com/sgl-project/sglang)
        Please note that the supported features and capabilities may vary between different endpoints and
        language models. Using features that are not supported by the endpoint will result in an error.

        This customization can be done by setting the `base_url` parameter to the base URL of the endpoint:
        ```python
        lm_invoker = OpenAILMInvoker(
            model_name="<model-name>",
            api_key="<your-api-key>",
            base_url="<https://base-url>",
        )
        result = await lm_invoker.invoke("Hi there!")
        ```

    Input types:
        The `OpenAILMInvoker` supports the following input types: text, document, and image.
        Non-text inputs can be passed as an `Attachment` object with the `user` role.

        Usage example:
        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Tool calling:
        Tool calling is a feature that allows the language model to call tools to perform tasks.
        Tools can be passed to the via the `tools` parameter as a list of `Tool` objects.
        When tools are provided and the model decides to call a tool, the tool calls are stored in the
        `tool_calls` attribute in the output.

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., tools=[tool_1, tool_2])
        ```

        Output example:
        ```python
        LMOutput(
            response="Let me call the tools...",
            tool_calls=[
                ToolCall(id="123", name="tool_1", args={"key": "value"}),
                ToolCall(id="456", name="tool_2", args={"key": "value"}),
            ]
        )
        ```

    Structured output:
        Structured output is a feature that allows the language model to output a structured response.
        This feature can be enabled by providing a schema to the `response_schema` parameter.

        The schema must be either a JSON schema dictionary or a Pydantic BaseModel class.
        If JSON schema is used, it must be compatible with Pydantic\'s JSON schema, especially for complex schemas.
        For this reason, it is recommended to create the JSON schema using Pydantic\'s `model_json_schema` method.

        The language model also doesn\'t need to stream anything when structured output is enabled. Thus, standard
        invocation will be performed regardless of whether the `event_emitter` parameter is provided or not.

        When enabled, the structured output is stored in the `structured_output` attribute in the output.
        1. If the schema is a JSON schema dictionary, the structured output is a dictionary.
        2. If the schema is a Pydantic BaseModel class, the structured output is a Pydantic model.

        # Example 1: Using a JSON schema dictionary
        Usage example:
        ```python
        schema = {
            "title": "Animal",
            "description": "A description of an animal.",
            "properties": {
                "color": {"title": "Color", "type": "string"},
                "name": {"title": "Name", "type": "string"},
            },
            "required": ["name", "color"],
            "type": "object",
        }
        lm_invoker = OpenAILMInvoker(..., response_schema=schema)
        ```
        Output example:
        ```python
        LMOutput(structured_output={"name": "Golden retriever", "color": "Golden"})
        ```

        # Example 2: Using a Pydantic BaseModel class
        Usage example:
        ```python
        class Animal(BaseModel):
            name: str
            color: str

        lm_invoker = OpenAILMInvoker(..., response_schema=Animal)
        ```
        Output example:
        ```python
        LMOutput(structured_output=Animal(name="Golden retriever", color="Golden"))
        ```

    Analytics tracking:
        Analytics tracking is a feature that allows the module to output additional information about the invocation.
        This feature can be enabled by setting the `output_analytics` parameter to `True`.
        When enabled, the following attributes will be stored in the output:
        1. `token_usage`: The token usage.
        2. `duration`: The duration in seconds.
        3. `finish_details`: The details about how the generation finished.

        Output example:
        ```python
        LMOutput(
            response="Golden retriever is a good dog breed.",
            token_usage=TokenUsage(
                input_tokens=1500,
                output_tokens=200,
                input_token_details=InputTokenDetails(cached_tokens=1200, uncached_tokens=300),
                output_token_details=OutputTokenDetails(reasoning_tokens=180, response_tokens=20),
            ),
            duration=0.729,
            finish_details={"status": "completed", "incomplete_details": {"reason": None}},
        )
        ```

    Retry and timeout:
        The `OpenAILMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=0, timeout=10.0)  # No retry, 10.0 seconds timeout
        retry_config = RetryConfig(max_retries=5, timeout=None)  # 5 max retries, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., retry_config=retry_config)
        ```

    Reasoning:
        OpenAI\'s GPT-5 models and o-series models are classified as reasoning models. Reasoning models think before
        they answer, producing a long internal chain of thought before responding to the user. Reasoning models
        excel in complex problem solving, coding, scientific reasoning, and multi-step planning for agentic workflows.

        The reasoning effort of reasoning models can be set via the `reasoning_effort` parameter. This parameter
        will guide the models on how many reasoning tokens it should generate before creating a response.
        Available options include:
        1. "minimal": Favors the least amount of reasoning, only supported for GPT-5 models onwards.
        2. "low": Favors speed and economical token usage.
        3. "medium": Favors a balance between speed and reasoning accuracy.
        4. "high": Favors more complete reasoning at the cost of more tokens generated and slower responses.
        When not set, the reasoning effort will be equivalent to `medium` by default.

        OpenAI doesn\'t expose the raw reasoning tokens. However, the summary of the reasoning tokens can still be
        generated. The summary level can be set via the `reasoning_summary` parameter. Available options include:
        1. "auto": The model decides the summary level automatically.
        2. "detailed": The model will generate a detailed summary of the reasoning tokens.
        Reasoning summary is not compatible with tool calling.
        When enabled, the reasoning summary will be stored in the `reasoning` attribute in the output.

        Output example:
        ```python
        LMOutput(
            response="Golden retriever is a good dog breed.",
            reasoning=[Reasoning(id="x", reasoning="Let me think about it...")],
        )
        ```

        Streaming output example:
        ```python
        {"type": "thinking_start", "value": ""}\', ...}
        {"type": "thinking", "value": "Let me think "}\', ...}
        {"type": "thinking", "value": "about it..."}\', ...}
        {"type": "thinking_end", "value": ""}\', ...}
        {"type": "response", "value": "Golden retriever ", ...}
        {"type": "response", "value": "is a good dog breed.", ...}
        ```
        Note: By default, the thinking token will be streamed with the legacy `EventType.DATA` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

        Setting reasoning-related parameters for non-reasoning models will raise an error.

    MCP tool calling:
        The `OpenAILMInvoker` supports MCP tool calling. This feature can be enabled by providing a list of
        MCP servers to the `mcp_servers` parameter. When MCP servers are provided and the model decides to call
        an MCP tool, the MCP calls are stored in the `mcp_calls` attribute in the output.

        Usage example:
        ```python
        from gllm_inference.schema import MCPServer
        mcp_server_1 = MCPServer(
            url="https://mcp_server_1.com",
            name="mcp_server_1",
        )
        lm_invoker = OpenAILMInvoker(..., mcp_servers=[mcp_server_1])
        ```

        Output example:
        ```python
        LMOutput(
            response="The result is 10.",
            mcp_calls=[
                MCPCall(
                    id="123",
                    server_name="mcp_server_1",
                    tool_name="mcp_tool_1",
                    args={"key": "value"},
                    output="The result is 10.",
                ),
            ],
        )
        ```

        Streaming output example:
        ```python
        {"type": "activity", "value": {"type": "mcp_list_tools", ...}, ...}
        {"type": "activity", "value": {"type": "mcp_call", ...}, ...}
        {"type": "response", "value": "The result ", ...}
        {"type": "response", "value": "is 10.", ...}
        ```
        Note: By default, the activity token will be streamed with the legacy `EventType.DATA` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

    Code interpreter:
        The code interpreter is a feature that allows the language model to write and run Python code in a
        sandboxed environment to solve complex problems in domains like data analysis, coding, and math.
        This feature can be enabled by setting the `code_interpreter` parameter to `True`.

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., code_interpreter=True)
        ```

        When code interpreter is enabled, it is highly recommended to instruct the model to use the "python tool"
        in the system message, as "python tool" is the term recognized by the model to refer to the code interpreter.

        Messages example:
        ```python
        messages = [
            Message.system("You are a data analyst. Use the python tool to generate a file."]),
            Message.user("Show an histogram of the following data: [1, 2, 1, 4, 1, 2, 4, 2, 3, 1]"),
        ]
        ```

        When code interpreter is enabled, the code execution results are stored in the `code_exec_results`
        attribute in the output.

        Output example:
        ```python
        LMOutput(
            response="The histogram is attached.",
            code_exec_results=[
                CodeExecResult(
                    id="123",
                    code="import matplotlib.pyplot as plt...",
                    output=[Attachment(data=b"...", mime_type="image/png")],
                ),
            ],
        )
        ```

        Streaming output example:
        ```python
        {"type": "code_start", "value": ""}\', ...}
        {"type": "code", "value": "import matplotlib"}\', ...}
        {"type": "code", "value": ".pyplot as plt..."}\', ...}
        {"type": "code_end", "value": ""}\', ...}
        {"type": "response", "value": "The histogram ", ...}
        {"type": "response", "value": "is attached.", ...}
        ```
        Note: By default, the code token will be streamed with the legacy `EventType.DATA` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

    Web search:
        The web search is a feature that allows the language model to search the web for relevant information.
        This feature can be enabled by setting the `web_search` parameter to `True`.

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., web_search=True)
        ```

        When web search is enabled, the language model will search the web for relevant information and may cite the
        relevant sources. The citations will be stored as `Chunk` objects in the `citations` attribute in the output.
        The content of the `Chunk` object is the type of the citation, e.g. "url_citation".

        Output example:
        ```python
        LMOutput(
            response="The winner of the match is team A ([Example title](https://www.example.com)).",
            citations=[
                Chunk(
                    id="123",
                    content="url_citation",
                    metadata={
                        "start_index": 164,
                        "end_index": 275,
                        "title": "Example title",
                        "url": "https://www.example.com",
                        "type": "url_citation",
                    },
                ),
            ],
        )
        ```

        Streaming output example:
        ```python
        {"type": "activity", "value": {"query": "search query"}, ...}
        {"type": "response", "value": "The winner of the match ", ...}
        {"type": "response", "value": "is team A ([Example title](https://www.example.com)).", ...}
        ```
        Note: By default, the activity token will be streamed with the legacy `EventType.DATA` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

    Output types:
        The output of the `OpenAILMInvoker` can either be:
        1. `str`: A text response.
        2. `LMOutput`: A Pydantic model that may contain the following attributes:
            2.1. response (str)
            2.2. tool_calls (list[ToolCall])
            2.3. structured_output (dict[str, Any] | BaseModel | None)
            2.4. token_usage (TokenUsage | None)
            2.5. duration (float | None)
            2.6. finish_details (dict[str, Any])
            2.7. reasoning (list[Reasoning])
            2.8. citations (list[Chunk])
            2.9. code_exec_results (list[CodeExecResult])
            2.10. mcp_calls (list[MCPCall])
    '''
    client_kwargs: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, base_url: str = ..., model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[Tool | LangChainTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, reasoning_effort: ReasoningEffort | None = None, reasoning_summary: ReasoningSummary | None = None, mcp_servers: list[MCPServer] | None = None, code_interpreter: bool = False, web_search: bool = False, simplify_events: bool = False) -> None:
        '''Initializes a new instance of the OpenAILMInvoker class.

        Args:
            model_name (str): The name of the OpenAI model.
            api_key (str | None, optional): The API key for authenticating with OpenAI. Defaults to None, in which
                case the `OPENAI_API_KEY` environment variable will be used. If the endpoint does not require an
                API key, a dummy value can be passed (e.g. "<empty>").
            base_url (str, optional): The base URL of a custom endpoint that is compatible with OpenAI\'s
                Responses API schema. Defaults to OpenAI\'s default URL.
            model_kwargs (dict[str, Any] | None, optional): Additional model parameters. Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            tools (list[Tool | LangChainTool] | None, optional): Tools provided to the model to enable tool calling.
                Defaults to None, in which case an empty list is used.
            response_schema (ResponseSchema | None, optional): The schema of the response. If provided, the model will
                output a structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema
                dictionary. Defaults to None.
            output_analytics (bool, optional): Whether to output the invocation analytics. Defaults to False.
            retry_config (RetryConfig | None, optional): The retry configuration for the language model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            reasoning_effort (ReasoningEffort | None, optional): The reasoning effort for reasoning models. Not allowed
                for non-reasoning models. If None, the model will perform medium reasoning effort. Defaults to None.
            reasoning_summary (ReasoningSummary | None, optional): The reasoning summary level for reasoning models.
                Not allowed for non-reasoning models. If None, no summary will be generated. Defaults to None.
            mcp_servers (list[MCPServer] | None, optional): The MCP servers containing tools to be accessed by the
                language model. Defaults to None.
            code_interpreter (bool, optional): Whether to enable the code interpreter. Defaults to False.
            web_search (bool, optional): Whether to enable the web search. Defaults to False.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.

        Raises:
            ValueError:
            1. `reasoning_effort` is provided, but is not a valid ReasoningEffort.
            2. `reasoning_summary` is provided, but is not a valid ReasoningSummary.
        '''
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the OpenAI language model.

        This method sets the response schema for the OpenAI language model. Any existing response schema will be
        replaced.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.
        """
