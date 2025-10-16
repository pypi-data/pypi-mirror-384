from _typeshed import Incomplete
from gllm_core.event import EventEmitter as EventEmitter
from gllm_core.schema.tool import Tool as Tool
from gllm_core.utils.retry import RetryConfig as RetryConfig
from gllm_inference.constants import GRPC_ENABLE_RETRIES_KEY as GRPC_ENABLE_RETRIES_KEY, INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, InvokerRuntimeError as InvokerRuntimeError, build_debug_info as build_debug_info
from gllm_inference.exceptions.provider_error_map import GRPC_STATUS_CODE_MAPPING as GRPC_STATUS_CODE_MAPPING
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.lm_invoker.schema.xai import Key as Key, ReasoningEffort as ReasoningEffort
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, LMOutput as LMOutput, Message as Message, MessageRole as MessageRole, ModelId as ModelId, ModelProvider as ModelProvider, Reasoning as Reasoning, ResponseSchema as ResponseSchema, ThinkingEvent as ThinkingEvent, TokenUsage as TokenUsage, ToolCall as ToolCall, ToolResult as ToolResult
from gllm_inference.utils.validation import validate_string_enum as validate_string_enum
from langchain_core.tools import Tool as LangChainTool
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete

class XAILMInvoker(BaseLMInvoker):
    '''A language model invoker to interact with xAI language models.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        client_params (dict[str, Any]): The xAI client initialization parameters.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Tool]): The list of tools provided to the model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig | None): The retry configuration for the language model.
        reasoning_effort (ReasoningEffort | None): The reasoning effort level for reasoning models ("low" or "high").
        web_search (bool): Whether to enable the web search.


    Basic usage:
        The `XAILMInvoker` can be used as follows:
        ```python
        lm_invoker = XAILMInvoker(model_name="grok-3")
        result = await lm_invoker.invoke("Hi there!")
        ```

    Input types:
        The `XAILMInvoker` supports the following input types: text and image.
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
        lm_invoker = XAILMInvoker(..., tools=[tool_1, tool_2])
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
        lm_invoker = XAILMInvoker(..., response_schema=schema)
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

        lm_invoker = XAILMInvoker(..., response_schema=Animal)
        ```
        Output example:
        ```python
        LMOutput(structured_output=Animal(name="Golden retriever", color="Golden"))
        ```

    Reasoning:
        Reasoning effort is a feature specific to xAI\'s reasoning models that allows you to control the level
        of reasoning performed by the model. This feature can be enabled by setting the `reasoning_effort` parameter.
        Valid values are "low" and "high".

        Please note that Grok 4 does not have a `reasoning_effort` parameter. If a `reasoning_effort` is provided,
        the request will return error.

        Usage example:
        ```python
        lm_invoker = XAILMInvoker(
            model_name="grok-3",
            reasoning_effort="high"  # Enable high reasoning effort
        )
        ```

        When reasoning effort is enabled, the model\'s internal reasoning process is captured and stored in the
        `reasoning` attribute in the output.

        Output example:
        ```python
        LMOutput(
            response="The answer is 42",
            reasoning=[
                Reasoning(
                    id="reasoning_1",
                    reasoning="First, I need to understand the question. The user is asking about..."
                )
            ]
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

    Analytics tracking:
        Analytics tracking is a feature that allows the module to output additional information about the invocation.
        This feature can be enabled by setting the `output_analytics` parameter to `True`.
        When enabled, the following attributes will be stored in the output:
        1. `token_usage`: The token usage.
        2. `finish_details`: The details about how the generation finished.

        Output example:
        ```python
        LMOutput(
            response="Golden retriever is a good dog breed.",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            finish_details={"finish_reason": "stop"},
        )
        ```

        When streaming is enabled, token usage is not supported. Therefore, the `token_usage` attribute will be `None`
        regardless of the value of the `output_analytics` parameter.

    Retry and timeout:
        The `XAILMInvoker` supports retry and timeout configuration.
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
        lm_invoker = XAILMInvoker(..., retry_config=retry_config)
        ```

    Web Search:
        The web search is a feature that allows the language model to search the web for relevant information.
        This feature can be enabled by setting the `web_search` parameter to `True`.

        Usage example:
        ```python
        lm_invoker = XAILMInvoker(
            model_name="grok-3",
            web_search=True
        )
        ```

        When web search is enabled, the language model will search for relevant information and may cite the
        relevant sources (including from X platform). The citations will be stored as `Chunk` objects in the
        `citations` attribute in the output.

        Output example:
        ```python
        LMOutput(
            response="According to recent reports, the latest AI developments... ([Source](https://example.com)).",
            citations=[
                Chunk(
                    id="search_result_1",
                    content="Latest AI developments report",
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

    Output types:
        The output of the `XAILMInvoker` can either be:
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
    '''
    reasoning_effort: Incomplete
    web_search: Incomplete
    client_params: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[Tool | LangChainTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, reasoning_effort: ReasoningEffort | None = None, web_search: bool = False, simplify_events: bool = False) -> None:
        """Initializes a new instance of the XAILMInvoker class.

        Args:
            model_name (str): The name of the xAI model.
            api_key (str | None, optional): The API key for authenticating with xAI. Defaults to None, in which
                case the `XAI_API_KEY` environment variable will be used.
            model_kwargs (dict[str, Any] | None, optional): Additional model parameters. Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            tools (list[Tool | LangChainTool] | None, optional): Tools provided to the language model to enable tool
            calling.
                Defaults to None.
            response_schema (ResponseSchema | None, optional): The schema of the response. If provided, the model will
                output a structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema
                dictionary. Defaults to None.
            output_analytics (bool, optional): Whether to output the invocation analytics. Defaults to False.
            retry_config (RetryConfig | None, optional): The retry configuration for the language model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout is used.
            reasoning_effort (ReasoningEffort | None, optional): The reasoning effort for reasoning models. Not allowed
                for non-reasoning models. If None, the model will perform medium reasoning effort. Defaults to None.
            web_search (bool, optional): Whether to enable the web search. Defaults to False.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.

        Raises:
            ValueError:
            1. `reasoning_effort` is provided, but is not a valid ReasoningEffort.
        """
