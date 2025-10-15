from _typeshed import Incomplete
from gllm_core.event import EventEmitter as EventEmitter
from gllm_core.schema.tool import Tool as Tool
from gllm_core.utils.retry import RetryConfig as RetryConfig
from gllm_inference.constants import INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.lm_invoker.schema.anthropic import InputType as InputType, Key as Key, OutputType as OutputType
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, BatchStatus as BatchStatus, LMInput as LMInput, LMOutput as LMOutput, Message as Message, ModelId as ModelId, ModelProvider as ModelProvider, Reasoning as Reasoning, ResponseSchema as ResponseSchema, ThinkingEvent as ThinkingEvent, TokenUsage as TokenUsage, ToolCall as ToolCall, ToolResult as ToolResult
from langchain_core.tools import Tool as LangChainTool
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
DEFAULT_MAX_TOKENS: int
DEFAULT_THINKING_BUDGET: int
BATCH_STATUS_MAP: Incomplete

class AnthropicLMInvoker(BaseLMInvoker):
    '''A language model invoker to interact with Anthropic language models.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        client (AsyncAnthropic): The Anthropic client instance.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Tool]): Tools provided to the model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig): The retry configuration for the language model.
        thinking (bool): Whether to enable thinking. Only allowed for thinking models.
        thinking_budget (int): The tokens allocated for the thinking process. Only allowed for thinking models.

    Basic usage:
        The `AnthropicLMInvoker` can be used as follows:
        ```python
        lm_invoker = AnthropicLMInvoker(model_name="claude-sonnet-4-20250514")
        result = await lm_invoker.invoke("Hi there!")
        ```

    Input types:
        The `AnthropicLMInvoker` supports the following input types: text, image, and document.
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
        lm_invoker = AnthropicLMInvoker(..., tools=[tool_1, tool_2])
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

        Structured output is achieved by providing the schema name in the `tool_choice` parameter. This forces
        the model to call the provided schema as a tool. Thus, structured output is not compatible with:
        1. Tool calling, since the tool calling is reserved to force the model to call the provided schema as a tool.
        2. Thinking, since thinking is not allowed when a tool use is forced through the `tool_choice` parameter.
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
        lm_invoker = AnthropicLMInvoker(..., response_schema=schema)
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

        lm_invoker = AnthropicLMInvoker(..., response_schema=Animal)
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
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            duration=0.729,
            finish_details={"stop_reason": "end_turn"},
        )
        ```

    Retry and timeout:
        The `AnthropicLMInvoker` supports retry and timeout configuration.
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
        lm_invoker = AnthropicLMInvoker(..., retry_config=retry_config)
        ```

    Thinking:
        Thinking is a feature that allows the language model to have enhanced reasoning capabilities for complex tasks,
        while also providing transparency into its step-by-step thought process before it delivers its final answer.
        This feature is only available for certain models, starting from Claude 3.7 Sonnet.
        It can be enabled by setting the `thinking` parameter to `True`.

        When thinking is enabled, the amount of tokens allocated for the thinking process can be set via the
        `thinking_budget` parameter. The `thinking_budget`:
        1. Must be greater than or equal to 1024.
        2. Must be less than the `max_tokens` hyperparameter, as the `thinking_budget` is allocated from the
           `max_tokens`. For example, if `max_tokens=2048` and `thinking_budget=1024`, the language model will
           allocate at most 1024 tokens for thinking and the remaining 1024 tokens for generating the response.

        When enabled, the reasoning is stored in the `reasoning` attribute in the output.

        Usage example:
        ```python
        lm_invoker = AnthropicLMInvoker(..., thinking=True, thinking_budget=1024)
        ```

        Output example:
        ```python
        LMOutput(
            response="Golden retriever is a good dog breed.",
            reasoning=[Reasoning(type="thinking", reasoning="Let me think about it...", signature="x")],
        )
        ```

        Streaming output example:
        ```python
        {"type": "thinking_start", "value": "", ...}
        {"type": "thinking", "value": "Let me think "\', ...}
        {"type": "thinking", "value": "about it..."}\', ...}
        {"type": "thinking_end", "value": ""}\', ...}
        {"type": "response", "value": "Golden retriever ", ...}
        {"type": "response", "value": "is a good dog breed.", ...}
        ```
        Note: By default, the thinking token will be streamed with the legacy `EventType.DATA` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

    Batch processing:
        The `AnthropicLMInvoker` supports batch processing, which allows the language model to process multiple
        requests in a single call. Batch processing is supported through the `batch` attribute.

        Usage example:
        ```python
        requests = {"request_1": "What color is the sky?", "request_2": "What color is the grass?"}
        results = await lm_invoker.batch.invoke(requests)
        ```

        Output example:
        ```python
        {
            "request_1": LMOutput(response="The sky is blue."),
            "request_2": LMOutput(finish_details={"type": "error", "error": {"message": "...", ...}, ...}),
        }
        ```

        The `AnthropicLMInvoker` also supports the following standalone batch processing operations:

        1. Create a batch job:
            ```python
            requests = {"request_1": "What color is the sky?", "request_2": "What color is the grass?"}
            batch_id = await lm_invoker.batch.create(requests)
            ```

        2. Get the status of a batch job:
            ```python
            status = await lm_invoker.batch.status(batch_id)
            ```

        3. Retrieve the results of a batch job:
            ```python
            results = await lm_invoker.batch.retrieve(batch_id)
            ```

            Output example:
            ```python
            {
                "request_1": LMOutput(response="The sky is blue."),
                "request_2": LMOutput(finish_details={"type": "error", "error": {"message": "...", ...}, ...}),
            }
            ```

        4. List the batch jobs:
            ```python
            batch_jobs = await lm_invoker.batch.list()
            ```

            Output example:
            ```python
            [
                {"id": "batch_123", "status": "finished"},
                {"id": "batch_456", "status": "in_progress"},
                {"id": "batch_789", "status": "canceling"},
            ]
            ```

        5. Cancel a batch job:
            ```python
            await lm_invoker.batch.cancel(batch_id)
            ```

    Output types:
        The output of the `AnthropicLMInvoker` can either be:
        1. `str`: A text response.
        2. `LMOutput`: A Pydantic model that may contain the following attributes:
            2.1. response (str)
            2.2. tool_calls (list[ToolCall])
            2.3. structured_output (dict[str, Any] | BaseModel | None)
            2.4. token_usage (TokenUsage | None)
            2.5. duration (float | None)
            2.6. finish_details (dict[str, Any])
            2.7. reasoning (list[Reasoning])
    '''
    client: Incomplete
    thinking: Incomplete
    thinking_budget: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[Tool | LangChainTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, thinking: bool = False, thinking_budget: int = ..., simplify_events: bool = False) -> None:
        """Initializes the AnthropicLmInvoker instance.

        Args:
            model_name (str): The name of the Anthropic language model.
            api_key (str | None, optional): The Anthropic API key. Defaults to None, in which case the
                `ANTHROPIC_API_KEY` environment variable will be used.
            model_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the Anthropic client.
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
            thinking (bool, optional): Whether to enable thinking. Only allowed for thinking models. Defaults to False.
            thinking_budget (int, optional): The tokens allocated for the thinking process. Must be greater than or
                equal to 1024. Only allowed for thinking models. Defaults to DEFAULT_THINKING_BUDGET.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.

        Raises:
            ValueError:
            1. `thinking` is True, but the `thinking_budget` is less than 1024.
            3. `response_schema` is provided, but `tools` or `thinking` are also provided.
        """
    def set_tools(self, tools: list[Tool | LangChainTool]) -> None:
        """Sets the tools for the Anthropic language model.

        This method sets the tools for the Anthropic language model. Any existing tools will be replaced.

        Args:
            tools (list[Tool | LangChainTool]): The list of tools to be used.

        Raises:
            ValueError: If `response_schema` exists.
        """
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the Anthropic language model.

        This method sets the response schema for the Anthropic language model. Any existing response schema will be
        replaced.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.

        Raises:
            ValueError: If `tools` exists.
        """
