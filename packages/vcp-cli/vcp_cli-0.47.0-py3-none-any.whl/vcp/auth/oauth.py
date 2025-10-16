import base64
import getpass
import hashlib
import hmac
import os
import secrets
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

import boto3
import jwt
import requests
from botocore.exceptions import ClientError
from pydantic import BaseModel
from rich.console import Console

from ..utils.token import TokenManager, TokenStore
from .config import AuthConfig, LogoutConfig

console = Console()


def compute_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    message = username + client_id
    dig = hmac.new(
        client_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


class AuthCode(BaseModel):
    """
    Represents the result of an OAuth2 authorization code flow.

    Attributes:
        code: The authorization code returned by the OAuth provider.
        verfier: The PKCE code verifier used in the flow.
        error: Any error message returned during the authorization process.
    """

    code: str
    verfier: str
    error: Optional[str]


# log in directly to congito from username and password
def get_tokens_password(
    config: AuthConfig, verbose: bool = False
) -> Optional[TokenStore]:
    """Get tokens directly from AWS Cognito using username/password."""
    try:
        if verbose:
            console.print("\n[bold blue]Starting direct authentication...[/bold blue]")
            console.print(f"User Pool ID: {config.user_pool_id}")
            console.print(f"Client ID: {config.client_id}")
            console.print(f"Region: {config.region}")

        if not config.username:
            raise ValueError("Username is required for authentication")

        # Prompt for password securely
        password = os.getenv("VCP_PASSWORD")
        if not password:
            password = getpass.getpass("Enter your password: ")

        # Create Cognito client
        cognito = boto3.client("cognito-idp", region_name=config.region)

        # Prepare AuthParameters
        auth_params = {"USERNAME": config.username, "PASSWORD": password}
        if config.client_secret:
            auth_params["SECRET_HASH"] = compute_secret_hash(
                config.username, config.client_id, config.client_secret
            )

        # Authenticate user
        response = cognito.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            ClientId=config.client_id,
            AuthParameters=auth_params,
        )

        if verbose:
            console.print("\n[bold green]Authentication successful![/bold green]")
            console.print("Received tokens:")
            for token_type in ["AccessToken", "IdToken", "RefreshToken"]:
                if token_type in response["AuthenticationResult"]:
                    console.print(
                        f"  {token_type}: {len(response['AuthenticationResult'][token_type])} characters"
                    )
            console.print(
                f"  ExpiresIn: {response['AuthenticationResult'].get('ExpiresIn', 'N/A')} seconds"
            )

        # Convert response to match the format expected by the rest of the application
        tokens = TokenStore(
            access_token=response["AuthenticationResult"]["AccessToken"],
            id_token=response["AuthenticationResult"]["IdToken"],
            refresh_token=response["AuthenticationResult"]["RefreshToken"],
            expires_in=response["AuthenticationResult"]["ExpiresIn"],
        )

        TokenManager().save_tokens(tokens)
        return tokens

    except Exception as e:
        if verbose:
            console.print("\n[bold red]Authentication Error:[/bold red]")
            console.print(traceback.format_exc())
        console.print(f"[red]Failed to get tokens: {str(e)}[/red]")
        return None


# log in through interactive authentication web interface
def get_tokens_web(config: AuthConfig, verbose: bool = False) -> Optional[TokenStore]:
    # prompt user with interactive web interface
    auth: AuthCode = get_auth_code(config, verbose)

    # log issues and exit
    if auth.error:
        console.print("\n[bold red]Authentication Error:[/bold red]")
        console.print(f"\t{auth.error}")
        return None

    # exchange authorization code for session token
    data = {
        "grant_type": "authorization_code",
        "code": auth.code,
        "redirect_uri": config.redirect_uri,
        "client_id": config.client_id,
        "code_verifier": auth.verfier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if config.client_secret:
        basic = base64.b64encode(
            f"{config.client_id}:{config.client_secret}".encode()
        ).decode()
        headers["Authorization"] = f"Basic {basic}"
    response = requests.post(
        f"https://{config.domain}/oauth2/token", data=data, headers=headers, timeout=30
    ).json()

    return TokenStore(
        access_token=response.get("access_token", None),
        id_token=response.get("id_token", None),
        refresh_token=response.get("refresh_token", None),
        expires_in=response.get("expires_in", 3600),
    )


# log in entrypoint based on user configuration
def login(config: AuthConfig, verbose: bool = False) -> Optional[TokenStore]:
    """Perform login based on user configuration"""
    if config.flow == "password":
        return get_tokens_password(config, verbose)
    elif config.flow == "web":
        return get_tokens_web(config, verbose)
    return None


class AuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    error = None

    def do_GET(self):
        """Handle the callback from AWS Cognito."""

        query = parse_qs(urlparse(self.path).query)

        if "code" in query:
            AuthCallbackHandler.auth_code = query["code"][0]
        elif "error" in query:
            AuthCallbackHandler.error = query["error"][0]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if AuthCallbackHandler.auth_code:
            self.wfile.write(b"Login successful! You can close this window.")
        else:
            self.wfile.write(
                b"Login failed! Please check the console for more information."
            )


# open browser, prompt user to add credentials for login - return auth code, verifier and error
def get_auth_code(config: AuthConfig, verbose: bool = True) -> AuthCode:
    """Launch interactive web browser into which user adds username/passowrd"""
    # start local server
    server = HTTPServer(
        (config.redirect_host, config.redirect_port), AuthCallbackHandler
    )

    # generate PKCE values
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )

    # build authorization URL
    auth_url = (
        f"https://{config.domain}/oauth2/authorize?"
        f"client_id={config.client_id}&"
        f"response_type=code&"
        f"scope={'+'.join(config.scopes)}&"
        f"redirect_uri={config.redirect_uri}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256"
    )

    # Open browser
    webbrowser.open(auth_url)

    # wait for callback in a thread (otherwise, the server blocks execution even after shutodwn)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    while AuthCallbackHandler.auth_code is None:
        time.sleep(0.2)
    server.shutdown()

    return AuthCode(
        code=AuthCallbackHandler.auth_code,
        verfier=code_verifier,
        error=AuthCallbackHandler.error,
    )


def refresh_tokens(
    config: AuthConfig, refresh_token: str, verbose: bool = False
) -> Optional[TokenStore]:
    """Refresh expired access tokens using the refresh token."""
    try:
        if verbose:
            console.print("\n[bold blue]Refreshing tokens...[/bold blue]")
            console.print(f"Region: {config.region}")

        # Create Cognito client
        cognito = boto3.client("cognito-idp", region_name=config.region)

        # Prepare request parameters for refresh
        auth_params = {"REFRESH_TOKEN": refresh_token}

        # Add secret hash if client secret is available
        if config.client_secret and config.username:
            auth_params["SECRET_HASH"] = compute_secret_hash(
                config.username, config.client_id, config.client_secret
            )

        # Refresh tokens using REFRESH_TOKEN_AUTH flow
        response = cognito.initiate_auth(
            AuthFlow="REFRESH_TOKEN_AUTH",
            ClientId=config.client_id,
            AuthParameters=auth_params,
        )

        if verbose:
            console.print("[bold green]Tokens refreshed successfully![/bold green]")
            console.print("New tokens:")
            for token_type in ["AccessToken", "IdToken"]:
                if token_type in response["AuthenticationResult"]:
                    console.print(
                        f"  {token_type}: {len(response['AuthenticationResult'][token_type])} characters"
                    )
            console.print(
                f"  ExpiresIn: {response['AuthenticationResult'].get('ExpiresIn', 'N/A')} seconds"
            )

        # Create new TokenStore with refreshed tokens
        # Use new refresh token if provided, otherwise keep the original
        new_refresh_token = response["AuthenticationResult"].get(
            "RefreshToken", refresh_token
        )
        tokens = TokenStore(
            access_token=response["AuthenticationResult"]["AccessToken"],
            id_token=response["AuthenticationResult"]["IdToken"],
            refresh_token=new_refresh_token,
            expires_in=response["AuthenticationResult"]["ExpiresIn"],
        )

        return tokens

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "NotAuthorizedException":
            if verbose:
                console.print("[yellow]Refresh token is invalid or expired[/yellow]")
        else:
            if verbose:
                console.print(f"[red]AWS Cognito error: {error_code}[/red]")
    except Exception as e:
        if verbose:
            console.print("\n[bold red]Token Refresh Error:[/bold red]")
            console.print(traceback.format_exc())
        console.print(f"[red]Failed to refresh tokens: {str(e)}[/red]")


def logout(config: LogoutConfig, verbose: bool = False) -> bool:
    """Perform logout by invalidating tokens with AWS Cognito."""
    try:
        # Load current tokens to get the access token for logout
        token_manager = TokenManager()
        tokens = token_manager.load_tokens()

        if not tokens:
            if verbose:
                console.print("[yellow]No active tokens found to invalidate[/yellow]")
            return True

        if verbose:
            console.print("\n[bold blue]Starting logout process...[/bold blue]")
            console.print(f"Region: {config.region}")

        # Create Cognito client
        cognito = boto3.client("cognito-idp", region_name=config.region)

        # Perform global sign out to invalidate all tokens for this user
        cognito.global_sign_out(AccessToken=tokens.access_token)

        if verbose:
            console.print(
                "[bold green]Successfully invalidated tokens with Cognito[/bold green]"
            )

        # Clear local tokens after successful Cognito logout
        token_manager.clear_tokens()

        if verbose:
            console.print("[bold green]Cleared local token storage[/bold green]")

        return True

    except cognito.exceptions.NotAuthorizedException:
        if verbose:
            console.print("[yellow]Tokens were already invalid or expired[/yellow]")
        # Still clear local tokens even if Cognito says they're invalid
        TokenManager().clear_tokens()
        return True

    except Exception as e:
        console.print(f"[red]Error during logout: {str(e)}[/red]")
        if verbose:
            console.print(traceback.format_exc())

        # If Cognito logout fails, still try to clear local tokens as fallback
        try:
            TokenManager().clear_tokens()
            console.print(
                "[yellow]Cleared local tokens despite Cognito logout failure[/yellow]"
            )
        except Exception as local_error:
            console.print(
                f"[red]Failed to clear local tokens: {str(local_error)}[/red]"
            )

        return False


def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Extract user information from the access token."""
    try:
        # Decode the token without verification to get the claims
        claims = jwt.decode(access_token, options={"verify_signature": False})

        # Extract username from claims
        username = claims.get("username") or claims.get("sub", "unknown")

        return {
            "username": username,
            "email": claims.get("email", ""),
            "email_verified": claims.get("email_verified", False),
        }
    except Exception as e:
        console.print(f"[red]Error extracting user info from token: {str(e)}[/red]")
        return None
