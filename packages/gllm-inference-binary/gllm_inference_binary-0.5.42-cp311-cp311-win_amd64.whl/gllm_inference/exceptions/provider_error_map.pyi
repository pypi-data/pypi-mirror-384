from _typeshed import Incomplete
from enum import IntEnum
from gllm_inference.exceptions.exceptions import APIConnectionError as APIConnectionError, APITimeoutError as APITimeoutError, BaseInvokerError as BaseInvokerError, ModelNotFoundError as ModelNotFoundError, ProviderAuthError as ProviderAuthError, ProviderConflictError as ProviderConflictError, ProviderInternalError as ProviderInternalError, ProviderInvalidArgsError as ProviderInvalidArgsError, ProviderOverloadedError as ProviderOverloadedError, ProviderRateLimitError as ProviderRateLimitError

class ExtendedHTTPStatus(IntEnum):
    """HTTP status codes outside of the standard HTTPStatus enum.

    Attributes:
        SERVICE_OVERLOADED (int): HTTP status code for service overloaded.
    """
    SERVICE_OVERLOADED = 529

HTTP_STATUS_TO_EXCEPTION_MAP: dict[int, type[BaseInvokerError]]
ANTHROPIC_ERROR_MAPPING: Incomplete
BEDROCK_ERROR_MAPPING: Incomplete
GOOGLE_ERROR_MAPPING: Incomplete
LANGCHAIN_ERROR_CODE_MAPPING: Incomplete
LITELLM_ERROR_MAPPING: Incomplete
OPENAI_ERROR_MAPPING: Incomplete
TWELVELABS_ERROR_MAPPING: Incomplete
VOYAGE_ERROR_MAPPING: Incomplete
GRPC_STATUS_CODE_MAPPING: Incomplete
ALL_PROVIDER_ERROR_MAPPINGS: Incomplete
