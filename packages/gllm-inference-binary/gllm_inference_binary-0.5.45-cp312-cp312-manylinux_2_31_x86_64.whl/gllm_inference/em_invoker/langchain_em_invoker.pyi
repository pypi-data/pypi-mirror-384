from _typeshed import Incomplete
from gllm_core.utils.retry import RetryConfig
from gllm_inference.constants import INVOKER_DEFAULT_TIMEOUT as INVOKER_DEFAULT_TIMEOUT, INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker as BaseEMInvoker
from gllm_inference.em_invoker.schema.langchain import Key as Key
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, InvokerRuntimeError as InvokerRuntimeError, build_debug_info as build_debug_info
from gllm_inference.exceptions.provider_error_map import ALL_PROVIDER_ERROR_MAPPINGS as ALL_PROVIDER_ERROR_MAPPINGS, LANGCHAIN_ERROR_CODE_MAPPING as LANGCHAIN_ERROR_CODE_MAPPING
from gllm_inference.schema import ModelId as ModelId, ModelProvider as ModelProvider, TruncationConfig as TruncationConfig, Vector as Vector
from gllm_inference.utils import load_langchain_model as load_langchain_model, parse_model_data as parse_model_data
from langchain_core.embeddings import Embeddings as Embeddings
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete

class LangChainEMInvoker(BaseEMInvoker):
    """A language model invoker to interact with LangChain's Embeddings.

    Attributes:
        model_id (str): The model ID of the embedding model.
        model_provider (str): The provider of the embedding model.
        model_name (str): The name of the embedding model.
        em (Embeddings): The instance to interact with an embedding model defined using LangChain's Embeddings.
        retry_config (RetryConfig): The retry configuration for the embedding model.
        truncation_config (TruncationConfig | None): The truncation configuration for the embedding model.
    """
    model: Incomplete
    def __init__(self, model: Embeddings | None = None, model_class_path: str | None = None, model_name: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, retry_config: RetryConfig | None = None, truncation_config: TruncationConfig | None = None) -> None:
        '''Initializes a new instance of the LangChainEMInvoker class.

        Args:
            model (Embeddings | None, optional): The LangChain\'s Embeddings instance. If provided, will take
                precedence over the `model_class_path` parameter. Defaults to None.
            model_class_path (str | None, optional): The LangChain\'s Embeddings class path. Must be formatted as
                "<package>.<class>" (e.g. "langchain_openai.OpenAIEmbeddings"). Ignored if `model` is provided.
                Defaults to None.
            model_name (str | None, optional): The model name. Only used if `model_class_path` is provided.
                Defaults to None.
            model_kwargs (dict[str, Any] | None, optional): The additional keyword arguments. Only used if
                `model_class_path` is provided. Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            retry_config (RetryConfig | None, optional): The retry configuration for the embedding model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            truncation_config (TruncationConfig | None, optional): Configuration for text truncation behavior.
                Defaults to None, in which case no truncation is applied.
        '''
