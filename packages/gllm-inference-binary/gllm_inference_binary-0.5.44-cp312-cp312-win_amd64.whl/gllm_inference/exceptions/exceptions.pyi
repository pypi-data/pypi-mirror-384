from _typeshed import Incomplete
from typing import Any

class BaseInvokerError(Exception):
    """Base exception class for all gllm_inference invoker errors."""
    debug_info: Incomplete
    class_name: Incomplete
    def __init__(self, class_name: str, message: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize the base exception.

        Args:
            class_name (str): The name of the class that raised the error.
            message (str): The error message.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """
    def verbose(self) -> str:
        """Verbose error message with debug information.

        Returns:
            str: The verbose error message with debug information.
        """

class ProviderInvalidArgsError(BaseInvokerError):
    """Exception for bad or malformed requests, invalid parameters or structure."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize ProviderInvalidArgsError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """

class ProviderAuthError(BaseInvokerError):
    """Exception for authorization failures due to API key issues."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize ProviderAuthError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """

class ProviderRateLimitError(BaseInvokerError):
    """Exception for rate limit violations."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize ProviderRateLimitError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """

class ProviderInternalError(BaseInvokerError):
    """Exception for unexpected server-side errors."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize ProviderInternalError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """

class ProviderOverloadedError(BaseInvokerError):
    """Exception for when the engine is currently overloaded."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize ProviderOverloadedError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """

class ModelNotFoundError(BaseInvokerError):
    """Exception for model not found errors."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize ModelNotFoundError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """

class APIConnectionError(BaseInvokerError):
    """Exception for when the client fails to connect to the model provider."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize APIConnectionError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """

class APITimeoutError(BaseInvokerError):
    """Exception for when the request to the model provider times out."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize APITimeoutError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """

class ProviderConflictError(BaseInvokerError):
    """Exception for when the request to the model provider conflicts."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize ProviderConflictError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """

class InvokerRuntimeError(BaseInvokerError):
    """Exception for runtime errors that occur during the invocation of the model."""
    def __init__(self, class_name: str, debug_info: dict[str, Any] | None = None) -> None:
        """Initialize the InvokerRuntimeError.

        Args:
            class_name (str): The name of the class that raised the error.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """
