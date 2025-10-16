"""
Centralized error handling utilities for VCP CLI.

This module provides consistent error handling patterns and user-friendly
error messages across all CLI commands.
"""

from functools import wraps
from typing import Any, Callable, Optional

import click
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from rich.console import Console

console = Console()


class VCPError(click.ClickException):
    """Base exception for VCP CLI errors."""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        super().__init__(message)
        self.suggestion = suggestion
        self.operation = operation

    def show(self, file=None):
        """Show error with Rich formatting."""
        console.print(f"[red]Error:[/red] {self.message}")
        if self.suggestion:
            console.print(f"[yellow]{self.suggestion}[/yellow]")
        if self.operation:
            console.print(
                f"Use [cyan]vcp {self.operation} --help[/cyan] for more information."
            )


class AuthenticationError(VCPError):
    """Raised when authentication is required or has failed."""

    def __init__(
        self, message: str = "Authentication required", operation: Optional[str] = None
    ):
        suggestion = "Please run 'vcp login' to authenticate."
        super().__init__(message, suggestion, operation)


class VCPPermissionError(VCPError):
    """Raised when user lacks permission for a resource."""

    def __init__(self, resource: str = "resource"):
        message = f"Access denied for {resource}"
        suggestion = "You don't have permission to access this resource. Contact your administrator or try searching for public datasets."
        super().__init__(message, suggestion)


class ResourceNotFoundError(VCPError):
    """Raised when a requested resource is not found."""

    def __init__(
        self, resource_type: str, resource_id: str, operation: Optional[str] = None
    ):
        message = f"{resource_type.title()} '{resource_id}' not found"
        suggestion = f"Please check that the {resource_type} ID is correct."
        super().__init__(message, suggestion, operation)


class NetworkError(VCPError):
    """Raised when network operations fail."""

    def __init__(self, message: str = "Network request failed"):
        suggestion = "Please check your internet connection and try again."
        super().__init__(message, suggestion)


class ServerError(VCPError):
    """Raised when server returns an error."""

    def __init__(self, status_code: Optional[int] = None):
        message = "Server error occurred"
        if status_code in (502, 503, 504):
            # Gateway errors and service unavailable - temporary issues
            suggestion = (
                "The service is temporarily unavailable. Please try again later."
            )
        else:
            # Other 5xx errors or unspecified
            suggestion = None
        super().__init__(message, suggestion)


class InvalidInputError(VCPError):
    """Raised when user input is invalid."""

    def __init__(
        self,
        input_type: str,
        details: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        message = f"Invalid {input_type}"
        if details:
            message += f": {details}"
        suggestion = f"Please check your {input_type} format and try again."
        super().__init__(message, suggestion, operation)


def handle_http_error(
    error: HTTPError,
    resource_type: str = "resource",
    resource_id: str = "",
    operation: Optional[str] = None,
) -> None:
    """
    Handle HTTP errors with user-friendly messages.

    Args:
        error: The HTTPError to handle
        resource_type: Type of resource being accessed (e.g., "dataset", "model")
        resource_id: ID of the resource being accessed
        operation: The operation context for --help reference
    """
    status_code = error.response.status_code

    if status_code == 401:
        raise AuthenticationError("Authentication failed", operation)
    elif status_code == 403:
        raise VCPPermissionError(
            f"{resource_type} '{resource_id}'" if resource_id else resource_type
        )
    elif status_code == 404:
        if resource_id:
            raise ResourceNotFoundError(resource_type, resource_id, operation)
        else:
            suggestion = "Please check your request and try again."
            raise VCPError(f"{resource_type.title()} not found", suggestion, operation)
    elif status_code >= 500:
        raise ServerError(status_code)
    else:
        raise ServerError()


def handle_request_error(error: RequestException) -> None:
    """
    Handle general request errors with user-friendly messages.

    Args:
        error: The RequestException to handle
    """
    if isinstance(error, Timeout):
        raise NetworkError("Request timed out")
    elif isinstance(error, ConnectionError):
        raise NetworkError("Unable to connect to the service")
    else:
        raise NetworkError(f"Request failed: {str(error)}")


def with_error_handling(resource_type: str = "resource", operation: str = "operation"):
    """
    Decorator that provides comprehensive error handling for CLI commands.

    Args:
        resource_type: Type of resource being operated on
        operation: Operation being performed
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except (VCPError, click.ClickException):
                # Re-raise VCP errors and Click exceptions as-is
                raise
            except HTTPError as e:
                # Extract resource_id from kwargs if available
                resource_id = (
                    kwargs.get("dataset_id")
                    or kwargs.get("model_id")
                    or kwargs.get("id", "")
                )
                handle_http_error(e, resource_type, resource_id, operation)
            except RequestException as e:
                handle_request_error(e)
            except FileNotFoundError as e:
                suggestion = "Please check the file path and ensure the file exists."
                if operation:
                    suggestion += (
                        f" Use 'vcp {operation} --help' for usage information."
                    )
                raise VCPError(
                    f"File not found: {str(e)}",
                    suggestion,
                ) from e
            except VCPPermissionError as e:
                suggestion = (
                    "Please check file permissions or run with appropriate privileges."
                )
                if operation:
                    suggestion += (
                        f" Use 'vcp {operation} --help' for usage information."
                    )
                raise VCPError(
                    f"Permission denied: {str(e)}",
                    suggestion,
                ) from e
            except Exception as e:
                suggestion = f"Details: {str(e)}\n\nIf this problem persists, please report it with the command details."
                if operation:
                    suggestion += (
                        f" Use 'vcp {operation} --help' for usage information."
                    )
                raise VCPError(
                    f"An unexpected error occurred during {operation}",
                    suggestion,
                ) from e

        return wrapper

    return decorator


def validate_dataset_id(dataset_id: str, operation: Optional[str] = None) -> None:
    """
    Validate dataset ID format.

    Args:
        dataset_id: The dataset ID to validate
        operation: The operation context for --help reference

    Raises:
        InvalidInputError: If the dataset ID format is invalid
    """
    if not dataset_id:
        raise InvalidInputError("dataset ID", "ID cannot be empty", operation)

    if len(dataset_id) < 20 or not all(c.isalnum() or c == "-" for c in dataset_id):
        raise InvalidInputError(
            "dataset ID",
            f"'{dataset_id}' is not a valid format. Dataset IDs should be long alphanumeric strings (20+ characters)",
            operation,
        )


def validate_search_term(term: str, operation: Optional[str] = None) -> None:
    """
    Validate search term.

    Args:
        term: The search term to validate
        operation: The operation context for --help reference

    Raises:
        InvalidInputError: If the search term is invalid
    """
    if not term or not term.strip():
        raise InvalidInputError("search term", "Search term cannot be empty", operation)


def check_authentication_status(tokens, operation: Optional[str] = None) -> None:
    """
    Check if user is authenticated.

    Args:
        tokens: Token object from TokenManager

    Raises:
        AuthenticationError: If user is not authenticated
    """
    if tokens is None:
        raise AuthenticationError("Not authenticated", operation)
