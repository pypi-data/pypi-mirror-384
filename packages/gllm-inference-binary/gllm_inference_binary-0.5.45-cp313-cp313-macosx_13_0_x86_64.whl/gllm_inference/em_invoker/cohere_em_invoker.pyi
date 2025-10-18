from _typeshed import Incomplete
from gllm_core.utils.retry import RetryConfig as RetryConfig
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker as BaseEMInvoker
from gllm_inference.em_invoker.schema.cohere import CohereInputType as CohereInputType, Key as Key
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, EMContent as EMContent, ModelId as ModelId, ModelProvider as ModelProvider, TruncationConfig as TruncationConfig, Vector as Vector
from gllm_inference.utils import validate_string_enum as validate_string_enum
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
MULTIMODAL_MODEL_VERSION: Incomplete

class CohereEMInvoker(BaseEMInvoker):
    '''An embedding model invoker to interact with Cohere embedding models.

    Attributes:
        model_id (str): The model ID of the embedding model.
        model_provider (str): The provider of the embedding model (Cohere).
        model_name (str): The name of the Cohere embedding model.
        client (AsyncClient): The asynchronous client for the Cohere API.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the embedding model.
        retry_config (RetryConfig): The retry configuration for the embedding model.
        truncation_config (TruncationConfig | None): The truncation configuration for the embedding model.
        input_type (CohereInputType): The input type for the embedding model. Supported values include:
            1. `CohereInputType.SEARCH_DOCUMENT`,
            2. `CohereInputType.SEARCH_QUERY`,
            3. `CohereInputType.CLASSIFICATION`,
            4. `CohereInputType.CLUSTERING`,
            5. `CohereInputType.IMAGE`.

    Initialization:
        You can initialize the `CohereEMInvoker` as follows:
        ```python
        em_invoker = CohereEMInvoker(
            model_name="embed-english-v4.0",
            input_type="search_document"
        )
        ```

        Note: The `input_type` parameter can be one of the following:
        1. "search_document"
        2. "search_query"
        3. "classification"
        4. "clustering"
        5. "image"

        This parameter is optional and defaults to "search_document". For more information about
        input_type, please refer to https://docs.cohere.com/docs/embeddings#the-input_type-parameter.

    Input types:
        The `CohereEMInvoker` supports the following input types: text and image.
        Non-text inputs must be passed as an `Attachment` object.

    Output format:
        The `CohereEMInvoker` can embed either:
        1. A single content.
           1. A single content is either a text or an image.
           2. The output will be a `Vector`, representing the embedding of the content.

           # Example 1: Embedding a text content.
           ```python
           text = "What animal is in this image?"
           result = await em_invoker.invoke(text)
           ```

           # Example 2: Embedding an image content.
           ```python
           image = Attachment.from_path("path/to/local/image.png")
           result = await em_invoker.invoke(image)
           ```

           The above examples will return a `Vector` with a size of (embedding_size,).

        2. A list of contents.
           1. A list of contents is a list that consists of any of the above single contents.
           2. The output will be a `list[Vector]`, where each element is a `Vector` representing the
              embedding of each single content.

           # Example: Embedding a list of contents.
           ```python
           text = "What animal is in this image?"
           image = Attachment.from_path("path/to/local/image.png")
           result = await em_invoker.invoke([text, image])
           ```

           The above examples will return a `list[Vector]` with a size of (2, embedding_size).

    Retry and timeout:
        The `CohereEMInvoker` supports retry and timeout configuration.
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
        em_invoker = CohereEMInvoker(..., retry_config=retry_config)
        ```

    '''
    input_type: Incomplete
    client: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, base_url: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, retry_config: RetryConfig | None = None, truncation_config: TruncationConfig | None = None, input_type: CohereInputType = ...) -> None:
        '''Initializes a new instance of the CohereEMInvoker class.

        Args:
            model_name (str): The name of the Cohere embedding model to be used.
            api_key (str | None, optional): The API key for authenticating with Cohere. Defaults to None, in which
                case the `COHERE_API_KEY` environment variable will be used.
            base_url (str | None, optional): The base URL for a custom Cohere-compatible endpoint.
                Defaults to None, in which case Cohere\'s default URL will be used.
            model_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the Cohere client.
                Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            retry_config (RetryConfig | None, optional): The retry configuration for the embedding model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            truncation_config (TruncationConfig | None, optional): Configuration for text truncation behavior.
                Defaults to None, in which case no truncation is applied.
            input_type (CohereInputType, optional): The input type for the embedding model.
                Defaults to `CohereInputType.SEARCH_DOCUMENT`. Valid values are: "search_document", "search_query",
                "classification", "clustering", and "image".
        '''
