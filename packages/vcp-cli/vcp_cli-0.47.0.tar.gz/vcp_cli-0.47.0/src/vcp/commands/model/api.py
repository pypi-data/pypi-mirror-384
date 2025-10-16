"""Model Hub API client.

This module provides API functions for interacting with the VCP Model Hub.
"""

from typing import Literal, Optional
from urllib.parse import urljoin

import requests

from vcp.utils.errors import AuthenticationError
from vcp.utils.token import TokenManager

from .models import ModelsListResponse


def _call_model_api(
    url: str,
    params: Optional[dict] = None,
    method: Literal["GET", "POST"] = "GET",
    json: Optional[dict] = None,
    timeout: float = 30,
) -> dict:
    """
    Make authenticated API call to Model Hub.

    Args:
        url: Full URL to call
        params: Optional query parameters
        method: HTTP method (GET or POST)
        json: Optional JSON body for POST requests
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response

    Raises:
        AuthenticationError: If not authenticated
        HTTPError: If HTTP error occurs (handled by CLI decorator)
        RequestException: If network error occurs (handled by CLI decorator)
    """
    token_manager = TokenManager()
    auth_headers = token_manager.get_auth_headers()

    if not auth_headers:
        raise AuthenticationError()

    response = requests.request(
        method, url, params=params, json=json, headers=auth_headers, timeout=timeout
    )
    response.raise_for_status()
    return response.json()


def fetch_models_list(modelhub_base_url: str) -> ModelsListResponse:
    """
    Fetch list of available models from Model Hub.

    Args:
        modelhub_base_url: Model Hub base URL

    Returns:
        ModelsListResponse containing list of models with their versions
    """
    url = urljoin(modelhub_base_url, "api/models/list")
    data = _call_model_api(url)
    return ModelsListResponse.model_validate(data)
