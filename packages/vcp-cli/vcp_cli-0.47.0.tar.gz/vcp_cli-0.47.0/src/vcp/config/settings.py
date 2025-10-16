"""Settings module for the VCP CLI."""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from .config import Config

load_dotenv()


class Settings(BaseModel):
    """Settings for the VCP CLI."""

    asset_hub_url: str
    aws_profile: str = os.getenv("VCP_AWS_PROFILE", "virtual-cell-dev-poweruser")
    aws_region: str
    s3_bucket: str = os.getenv("S3_BUCKET", "vcp-assets-pocs")
    s3_models_path: str = os.getenv("S3_MODELS_PATH", "models")
    cognito_user_pool_id: str = os.getenv("COGNITO_USER_POOL_ID", "test-pool")
    cognito_region: str = os.getenv("COGNITO_REGION", "us-east-1")


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the settings instance."""
    global _settings
    if _settings is None:
        config = Config.load()
        _settings = Settings(
            asset_hub_url=config.api.base_url, aws_region=config.aws.region
        )
    return _settings
