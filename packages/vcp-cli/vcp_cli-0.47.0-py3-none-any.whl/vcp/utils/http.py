"""HTTP utilities for making API requests with consistent behavior for user-agent, accept headers, and error handling."""

import functools
from json import JSONDecodeError
from typing import Any, Dict, Optional

import requests

from vcp import __version__
from vcp.commands.benchmarks.utils import CLIError
from vcp.utils.token import TokenManager


@functools.cache
def _get_session() -> requests.Session:
    """Get or create a shared session with VCP CLI user-agent header."""
    session = requests.Session()
    session.headers["User-Agent"] = get_user_agent()
    session.headers["Accept"] = "application/json"

    return session


def get_user_agent() -> str:
    """Get the user-agent string for VCP CLI requests.

    Returns:
        User-agent string in format "vcp-cli/{version}"
    """
    return f"vcp-cli/{__version__}"


def _validate_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Validate and prepare headers for HTTP requests.

    Args:
        headers: Optional headers dict

    Returns:
        Validated headers dict

    Raises:
        RuntimeError: If critical headers are being overridden
    """
    if headers is None:
        headers = {}

    # Prevent overriding critical headers
    if "User-Agent" in headers and headers["User-Agent"] != get_user_agent():
        raise RuntimeError("Cannot override User-Agent header")
    if "Accept" in headers and headers["Accept"] != "application/json":
        raise RuntimeError("Cannot override Accept header")

    return headers


def _add_auth_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Add authentication headers to the request.

    Args:
        headers: Existing headers dict

    Returns:
        Headers dict with auth headers added
    """
    token_manager = TokenManager()
    auth_headers = token_manager.get_auth_headers()
    if auth_headers:
        headers.update(auth_headers)
    return headers


def _handle_response(response: requests.Response, url: str) -> Any:
    """Handle HTTP response with consistent error handling and JSON parsing.

    Args:
        response: The HTTP response object
        url: The original request URL for error messages

    Returns:
        Parsed JSON data

    Raises:
        CLIError: For HTTP errors, authentication issues, or non-JSON responses
    """
    try:
        response.raise_for_status()

        # Require JSON response
        if not response.headers.get("content-type", "").startswith("application/json"):
            raise CLIError(
                f"Expected JSON response but got '{response.headers.get('content-type', 'unknown')}' from {url}"
            )

        data = response.json()
        return data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise CLIError("Authentication failed. Please run 'vcp login'.") from e
        elif e.response.status_code == 403:
            raise CLIError("Access denied. Check your permissions.") from e
        else:
            # Try to extract error details from JSON response
            try:
                if e.response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    error_data = e.response.json()
                    if isinstance(error_data, dict) and "detail" in error_data:
                        raise CLIError(f"API Error: {error_data['detail']}") from e
            except (ValueError, KeyError, AttributeError):
                # Failed to parse JSON or access attributes, fall back to generic error
                pass
            raise CLIError(f"HTTP Error: {e}") from e
    except requests.exceptions.Timeout as e:
        raise CLIError("Request timeout. Please check your connection.") from e
    except requests.exceptions.RequestException as e:
        raise CLIError("Request failed.") from e
    except JSONDecodeError as e:
        raise CLIError("Failed to parse JSON response.") from e


def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30,
    **kwargs: Any,
) -> Any:
    """Make a GET request with VCP CLI user-agent and require JSON response.

    Args:
        url: The URL to request
        params: Optional query parameters
        headers: Optional headers (user-agent and accept will be added/overridden)
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to requests.get

    Returns:
        Parsed JSON data

    Raises:
        CLIError: For HTTP errors, authentication issues, or non-JSON responses
    """
    headers = _validate_headers(headers)
    headers = _add_auth_headers(headers)

    response = _get_session().get(
        url, params=params, headers=headers, timeout=timeout, **kwargs
    )

    return _handle_response(response, url)


def post_json(
    url: str,
    data: Any = None,
    json: Any = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30,
    **kwargs: Any,
) -> Any:
    """Make a POST request with VCP CLI user-agent and require JSON response.

    Args:
        url: The URL to request
        data: Optional form data
        json: Optional JSON data
        params: Optional query parameters
        headers: Optional headers (user-agent and content-type will be added/overridden)
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to requests.post

    Returns:
        Parsed JSON data

    Raises:
        CLIError: For HTTP errors, authentication issues, or non-JSON responses
    """
    headers = _validate_headers(headers)
    headers = _add_auth_headers(headers)

    # Set content-type for JSON requests
    if json is not None:
        headers.setdefault("Content-Type", "application/json")

    response = _get_session().post(
        url,
        data=data,
        json=json,
        params=params,
        headers=headers,
        timeout=timeout,
        **kwargs,
    )

    return _handle_response(response, url)
