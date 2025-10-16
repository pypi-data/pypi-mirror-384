"""Token management utilities."""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field

from .encryption import decrypt, encrypt

logger = logging.getLogger(__name__)


class TokenStore(BaseModel):
    """
    Tokens to store for continuing an authenticated user session
    """

    access_token: str
    id_token: str
    refresh_token: Optional[str] = None
    expires_in: int = Field(default=3600)  # optional at runtime
    expires_at: int = Field(default=0)

    def model_post_init(self, __context):
        # Only set expires_at if it's not already set (e.g., when loading from storage)
        if self.expires_at == 0:
            self.expires_at = int(time.time()) + self.expires_in


class TokenManager:
    def __init__(self):
        self.token_file = Path.home() / ".vcp" / "tokens.json"
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Token file path: {self.token_file}")

    def save_tokens(self, tokens: TokenStore) -> None:
        """Save encrypted tokens with expiration."""

        try:
            logger.debug("Saving tokens")
            logger.debug(f"Token keys: {list(TokenStore.model_fields)}")

            # Convert to JSON string
            token_data = tokens.model_dump_json()
            logger.debug(f"Token data length before encryption: {len(token_data)}")

            # Encrypt and save
            encrypted_data = encrypt(token_data)
            logger.debug(f"Token data length after encryption: {len(encrypted_data)}")

            # Use write_bytes for encrypted data
            self.token_file.write_bytes(encrypted_data)
            logger.debug("Tokens saved successfully")

        except Exception as e:
            logger.error(f"Failed to save tokens: {str(e)}")
            if self.token_file.exists():
                self.token_file.unlink()
            raise

    def load_tokens(self) -> Optional[TokenStore]:
        """Load and decrypt tokens from storage."""
        try:
            if not self.token_file.exists():
                logger.debug("No token file found")
                return None

            # Read and decrypt
            encrypted_data = self.token_file.read_bytes()
            logger.debug(f"Read encrypted data length: {len(encrypted_data)}")

            token_data = decrypt(encrypted_data)
            logger.debug(f"Decrypted data length: {len(token_data)}")

            # Parse JSON
            tokens = json.loads(token_data)
            logger.debug(f"Loaded token keys: {list(tokens.keys())}")

            return TokenStore(**tokens)

        except Exception as e:
            logger.error(f"Failed to load tokens: {str(e)}")
            if self.token_file.exists():
                self.token_file.unlink()
            return None

    def refresh_tokens_if_needed(self, tokens: TokenStore) -> Optional[TokenStore]:
        """Check if tokens need refresh and refresh them if necessary."""
        # Check if tokens need refresh (expired or expiring within 5 minutes)
        current_time = time.time()
        expires_at = tokens.expires_at
        refresh_buffer = 300  # 5 minutes in seconds
        expires_within_5_minutes = expires_at and expires_at < (
            current_time + refresh_buffer
        )

        # Proactive refresh: refresh if token expires within 5 minutes OR already expired
        if expires_within_5_minutes:
            if expires_at < current_time:
                logger.info("Tokens have expired, attempting refresh...")
            else:
                time_until_expiry = (expires_at - current_time) / 60
                logger.info(
                    f"Tokens expire in {time_until_expiry:.1f} minutes, proactively refreshing..."
                )

            # Try to refresh tokens if refresh_token is available
            if tokens.refresh_token:
                refreshed_tokens = self._refresh_expired_tokens(tokens.refresh_token)
                if refreshed_tokens:
                    logger.info("Successfully refreshed tokens")
                    self.save_tokens(refreshed_tokens)
                    return refreshed_tokens
                else:
                    logger.info("Failed to refresh tokens, clearing stored tokens")
                    self.clear_tokens()
                    return None
            else:
                logger.info("No refresh token available, clearing tokens")
                self.clear_tokens()
                return None

        return tokens

    def _refresh_expired_tokens(self, refresh_token: str) -> Optional[TokenStore]:
        """Helper method to refresh expired tokens using the refresh token."""
        try:
            # Import here to avoid circular imports
            from ..auth.oauth import AuthConfig, refresh_tokens  # noqa: PLC0415
            from ..config.config import Config  # noqa: PLC0415

            config_data = Config.load()
            oauth_config = AuthConfig(
                user_pool_id=config_data.aws.cognito.user_pool_id,
                client_id=config_data.aws.cognito.client_id,
                client_secret=config_data.aws.cognito.client_secret,
                domain=config_data.aws.cognito.domain,
                region=config_data.aws.region,
                username=None,  # Not needed for refresh
                flow="refresh",  # Custom flow identifier
            )

            # Attempt to refresh tokens
            return refresh_tokens(oauth_config, refresh_token, verbose=False)

        except Exception as e:
            logger.error(f"Error during token refresh: {str(e)}")
            return None

    def get_auth_headers(
        self, include_content_type: bool = True
    ) -> Optional[Dict[str, str]]:
        """Get authentication headers with token and expiration info."""
        # Load tokens from storage
        tokens = self.load_tokens()
        if not tokens:
            return None

        # Check if tokens need refresh and refresh if necessary
        tokens = self.refresh_tokens_if_needed(tokens)
        if not tokens:
            return None

        headers = {
            "Authorization": f"Bearer {tokens.id_token}",
        }

        # Add Content-Type only if requested (not for multipart requests)
        if include_content_type:
            headers["Content-Type"] = "application/json"

        # Add expiration info for backend validation
        if tokens.expires_at:
            headers["X-Token-Expires-At"] = str(tokens.expires_at)

        return headers

    def clear_tokens(self) -> None:
        """Clear stored tokens."""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
                logger.info("Tokens cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear tokens: {str(e)}")
            raise
