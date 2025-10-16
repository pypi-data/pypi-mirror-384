from typing import Any, List, Optional

from pydantic import BaseModel, Field


class LogoutConfig(BaseModel):
    """Configuration for logout operations - only includes fields needed for token invalidation."""

    region: str


class AuthConfig(BaseModel):
    user_pool_id: str
    client_id: str
    client_secret: Optional[str] = None
    domain: str
    region: str
    username: Optional[str] = None
    password: Optional[str] = None
    flow: str = Field(default="password")  # "password", "web", or "refresh"
    redirect_uri: str = Field(default="http://localhost:3000/")
    scopes: List[str] = Field(default_factory=lambda: ["openid", "profile"])

    def model_post_init(self, context: Any) -> None:
        if self.flow == "password" and self.username is None:
            raise ValueError(
                "Username is required configuration when authenticating with password flow"
            )

    @property
    def redirect_host(self) -> str:
        return self.redirect_uri.split("//")[1].split(":")[0]

    @property
    def redirect_port(self) -> int:
        return int(self.redirect_uri.split("//")[1].split(":")[1].rstrip("/"))
