from gllm_inference.exceptions.exceptions import BaseInvokerError as BaseInvokerError, InvokerRuntimeError as InvokerRuntimeError
from gllm_inference.exceptions.provider_error_map import ALL_PROVIDER_ERROR_MAPPINGS as ALL_PROVIDER_ERROR_MAPPINGS, HTTP_STATUS_TO_EXCEPTION_MAP as HTTP_STATUS_TO_EXCEPTION_MAP
from typing import Any

def build_debug_info(error: Any, class_name: str) -> dict[str, Any]:
    """Build debug information for an error.

    Args:
        error (Any): The error to extract debug information from.
        class_name (str): The name of the class that raised the error.

    Returns:
        dict[str, Any]: A dictionary containing debug information about the error.
    """
def convert_http_status_to_base_invoker_error(error: Exception, invoker: BaseEMInvoker | BaseLMInvoker, status_code_extractor: callable = None, provider_error_mapping: dict[str, type[BaseInvokerError]] = ...) -> BaseInvokerError:
    """Extract provider error with HTTP status code fallback pattern.

    This function implements the common pattern used by Bedrock and Google invokers
    where they first try to extract HTTP status codes, then fall back to provider-specific
    error mappings based on exception keys.

    Args:
        error (Exception): The error to convert.
        invoker (BaseEMInvoker | BaseLMInvoker): The invoker instance that raised the error.
        status_code_extractor (callable): Function to extract status code from error.
        provider_error_mapping (dict): Provider-specific error mapping dictionary.

    Returns:
        BaseInvokerError: The converted error.
    """
def convert_to_base_invoker_error(error: Exception, invoker: BaseEMInvoker | BaseLMInvoker) -> BaseInvokerError:
    """Convert provider error into BaseInvokerError.

    Args:
        error (Exception): The error to convert.
        invoker (BaseEMInvoker | BaseLMInvoker): The invoker instance that raised the error.

    Returns:
        BaseInvokerError: The converted error.

    """
