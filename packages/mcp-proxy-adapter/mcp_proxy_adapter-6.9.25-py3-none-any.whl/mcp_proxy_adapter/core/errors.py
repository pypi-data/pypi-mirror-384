"""
Module for defining errors and exceptions for the microservice.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


class MicroserviceError(Exception):
    """
    Base class for all microservice exceptions.

    Attributes:
        message: Error message.
        code: Error code.
        data: Additional error data.
    """

    def __init__(
        self, message: str, code: int = -32000, data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the error.

        Args:
            message: Error message.
            code: Error code according to JSON-RPC standard.
            data: Additional error data.
        """
        self.message = message
        self.code = code
        self.data = data or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the error to a dictionary for JSON-RPC response.

        Returns:
            Dictionary with error information.
        """
        result = {"code": self.code, "message": self.message}

        if self.data:
            result["data"] = self.data

        return result


class ParseError(MicroserviceError):
    """
    Error while parsing JSON request.
    JSON-RPC Error code: -32700
    """

    def __init__(
        self, message: str = "Parse error", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=-32700, data=data)


class InvalidRequestError(MicroserviceError):
    """
    Invalid JSON-RPC request format.
    JSON-RPC Error code: -32600
    """

    def __init__(
        self, message: str = "Invalid Request", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=-32600, data=data)


class MethodNotFoundError(MicroserviceError):
    """
    Method not found error.
    JSON-RPC Error code: -32601
    """

    def __init__(
        self, message: str = "Method not found", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=-32601, data=data)


class InvalidParamsError(MicroserviceError):
    """
    Invalid method parameters.
    JSON-RPC Error code: -32602
    """

    def __init__(
        self, message: str = "Invalid params", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=-32602, data=data)


class InternalError(MicroserviceError):
    """
    Internal server error.
    JSON-RPC Error code: -32603
    """

    def __init__(
        self, message: str = "Internal error", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=-32603, data=data)


class ValidationError(MicroserviceError):
    """
    Input data validation error.
    JSON-RPC Error code: -32602 (using Invalid params code)
    """

    def __init__(
        self, message: str = "Validation error", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=-32602, data=data)


class CommandError(MicroserviceError):
    """
    Command execution error.
    JSON-RPC Error code: -32000 (server error)
    """

    def __init__(
        self,
        message: str = "Command execution error",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code=-32000, data=data)


class NotFoundError(MicroserviceError):
    """
    "Not found" error.
    JSON-RPC Error code: -32601 (using Method not found code)
    """

    def __init__(
        self, message: str = "Resource not found", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=-32601, data=data)


class ConfigurationError(MicroserviceError):
    """
    Configuration error.
    JSON-RPC Error code: -32603 (using Internal error code)
    """

    def __init__(
        self,
        message: str = "Configuration error",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code=-32603, data=data)


class AuthenticationError(MicroserviceError):
    """
    Authentication error.
    JSON-RPC Error code: -32001 (server error)
    """

    def __init__(
        self,
        message: str = "Authentication error",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code=-32001, data=data)


class AuthorizationError(MicroserviceError):
    """
    Authorization error.
    JSON-RPC Error code: -32002 (server error)
    """

    def __init__(
        self,
        message: str = "Authorization error",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code=-32002, data=data)


class TimeoutError(MicroserviceError):
    """
    Timeout error.
    JSON-RPC Error code: -32003 (server error)
    """

    def __init__(
        self, message: str = "Timeout error", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code=-32003, data=data)


def format_validation_errors(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Formats validation errors into a standard format.

    Args:
        errors: List of validation errors.

    Returns:
        Formatted validation errors.
    """
    formatted_errors = {}
    for error in errors:
        loc = error.get("loc", [])
        field = ".".join(str(item) for item in loc)
        msg = error.get("msg", "Validation error")
        formatted_errors[field] = msg
    return formatted_errors


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    level: str  # "error", "warning", "info"
    message: str
    section: Optional[str] = None
    key: Optional[str] = None
    suggestion: Optional[str] = None


class ConfigError(MicroserviceError):
    """Configuration validation error."""
    
    def __init__(self, message: str, validation_results: Optional[List[ValidationResult]] = None):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            validation_results: List of validation results that caused the error
        """
        super().__init__(message, code=-32001, data={"type": "configuration_error"})
        self.validation_results = validation_results or []
    
    def get_error_summary(self) -> str:
        """Get summary of all validation errors."""
        if not self.validation_results:
            return self.message
        
        error_messages = []
        for result in self.validation_results:
            if result.level == "error":
                location = f"{result.section}.{result.key}" if result.key else result.section
                error_msg = f"[{location}] {result.message}"
                if result.suggestion:
                    error_msg += f" (Suggestion: {result.suggestion})"
                error_messages.append(error_msg)
        
        return "\n".join(error_messages)


class MissingConfigKeyError(ConfigError):
    """Missing required configuration key."""
    
    def __init__(self, key: str, section: str = None):
        location = f"{section}.{key}" if section else key
        message = f"Required configuration key '{location}' is missing"
        super().__init__(message)
        self.key = key
        self.section = section


class InvalidConfigValueError(ConfigError):
    """Invalid configuration value."""
    
    def __init__(self, key: str, value: Any, expected_type: str, section: str = None):
        location = f"{section}.{key}" if section else key
        message = f"Invalid value for '{location}': got {type(value).__name__}, expected {expected_type}"
        super().__init__(message)
        self.key = key
        self.section = section
        self.value = value
        self.expected_type = expected_type


class MissingConfigSectionError(ConfigError):
    """Missing required configuration section."""
    
    def __init__(self, section: str):
        message = f"Required configuration section '{section}' is missing"
        super().__init__(message)
        self.section = section


class MissingConfigFileError(ConfigError):
    """Missing configuration file."""
    
    def __init__(self, file_path: str):
        message = f"Configuration file '{file_path}' does not exist"
        super().__init__(message)
        self.file_path = file_path


class InvalidConfigFileError(ConfigError):
    """Invalid configuration file format."""
    
    def __init__(self, file_path: str, reason: str):
        message = f"Invalid configuration file '{file_path}': {reason}"
        super().__init__(message)
        self.file_path = file_path
        self.reason = reason
