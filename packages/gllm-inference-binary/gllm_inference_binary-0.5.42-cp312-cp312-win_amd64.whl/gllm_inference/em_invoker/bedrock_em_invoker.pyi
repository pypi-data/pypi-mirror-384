from _typeshed import Incomplete
from enum import StrEnum
from gllm_core.utils.retry import RetryConfig as RetryConfig
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker as BaseEMInvoker
from gllm_inference.em_invoker.schema.bedrock import InputType as InputType, Key as Key, OutputType as OutputType
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, convert_http_status_to_base_invoker_error as convert_http_status_to_base_invoker_error
from gllm_inference.exceptions.provider_error_map import BEDROCK_ERROR_MAPPING as BEDROCK_ERROR_MAPPING
from gllm_inference.schema import ModelId as ModelId, ModelProvider as ModelProvider, TruncationConfig as TruncationConfig, Vector as Vector
from typing import Any

class ModelType(StrEnum):
    """Defines the type of the Bedrock embedding model."""
    COHERE = 'cohere'
    TITAN = 'titan'

SUPPORTED_ATTACHMENTS: Incomplete

class BedrockEMInvoker(BaseEMInvoker):
    '''An embedding model invoker to interact with AWS Bedrock embedding models.

    Attributes:
        model_id (str): The model ID of the embedding model.
        model_provider (str): The provider of the embedding model.
        model_name (str): The name of the embedding model.
        session (Session): The Bedrock client session.
        client_kwargs (dict[str, Any]): The Bedrock client kwargs.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the embedding model.
        retry_config (RetryConfig): The retry configuration for the embedding model.
        truncation_config (TruncationConfig | None): The truncation configuration for the embedding model.

    Input types:
        The `BedrockEMInvoker` only supports text inputs.

    Output format:
        The `BedrockEMInvoker` can embed either:
        1. A single content.
           1. A single content is a single text.
           2. The output will be a `Vector`, representing the embedding of the content.

           # Example 1: Embedding a text content.
           ```python
           text = "This is a text"
           result = await em_invoker.invoke(text)
           ```

           The above examples will return a `Vector` with a size of (embedding_size,).

        2. A list of contents.
           1. A list of contents is a list of texts.
           2. The output will be a `list[Vector]`, where each element is a `Vector` representing the
              embedding of each single content.

           # Example: Embedding a list of contents.
           ```python
           text1 = "This is a text"
           text2 = "This is another text"
           text3 = "This is yet another text"
           result = await em_invoker.invoke([text1, text2, text3])
           ```

           The above examples will return a `list[Vector]` with a size of (3, embedding_size).

    Retry and timeout:
        The `BedrockEMInvoker` supports retry and timeout configuration.
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
        em_invoker = BedrockEMInvoker(..., retry_config=retry_config)
        ```
    '''
    session: Incomplete
    client_kwargs: Incomplete
    def __init__(self, model_name: str, access_key_id: str | None = None, secret_access_key: str | None = None, region_name: str = 'us-east-1', model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, retry_config: RetryConfig | None = None, truncation_config: TruncationConfig | None = None) -> None:
        '''Initializes a new instance of the BedrockEMInvoker class.

        Args:
            model_name (str): The name of the Bedrock embedding model to be used.
            access_key_id (str | None, optional): The AWS access key ID. Defaults to None, in which case
                the `AWS_ACCESS_KEY_ID` environment variable will be used.
            secret_access_key (str | None, optional): The AWS secret access key. Defaults to None, in which case
                the `AWS_SECRET_ACCESS_KEY` environment variable will be used.
            region_name (str, optional): The AWS region name. Defaults to "us-east-1".
            model_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the Bedrock client.
                Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            retry_config (RetryConfig | None, optional): The retry configuration for the embedding model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            truncation_config (TruncationConfig | None, optional): Configuration for text truncation behavior.
                Defaults to None, in which case no truncation is applied.

        Raises:
            ValueError: If the model name is not supported.
            ValueError: If `access_key_id` or `secret_access_key` is neither provided nor set in the
                `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` environment variables, respectively.
        '''
