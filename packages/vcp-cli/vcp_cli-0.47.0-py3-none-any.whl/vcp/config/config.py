from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console

console = Console()


@dataclass
class CognitoConfig:
    user_pool_id: str
    client_id: str
    domain: str
    client_secret: Optional[str] = None
    region: str = "us-east-1"
    scopes: Optional[List[str]] = field(default_factory=lambda: ["openid", "profile"])
    flow: Optional[str] = "password"  # "password" or "web"


@dataclass
class GitHubConfig:
    contributions_org: str = "cz-model-contributions"
    template_repo: str = "git@github.com:chanzuckerberg/model-template.git"


@dataclass
class ModelsConfig:
    base_url: str
    github: GitHubConfig = field(default_factory=GitHubConfig)


@dataclass
class DataAPIConfig:
    base_url: str


@dataclass
class DatabricksConfig:
    host: str
    token: str


@dataclass
class AWSConfig:
    region: str
    cognito: CognitoConfig


@dataclass
class BenchmarksAPIEndpointsConfig:
    """model for benchmarks API endpoints configuration."""

    list_benchmarks: str = "/api/benchmarks"
    get_benchmarks_by_key: str = "/api/benchmarks/{benchmark_key}"
    get_benchmark_models: str = "/api/benchmarks/models/{model_key}"


@dataclass
class BenchmarksAPIConfig:
    base_url: str
    endpoints: BenchmarksAPIEndpointsConfig


@dataclass
class DataSubcommandFlags:
    credentials: bool = True


# NOTE: To set feature flags for production release, make edits in generate_config.py
@dataclass
class FeatureFlagsConfig:
    data_command: bool = True
    model_command: bool = True
    benchmarks_command: bool = True
    data_subcommands: DataSubcommandFlags = field(default_factory=DataSubcommandFlags)


@dataclass
class Config:
    feature_flags: FeatureFlagsConfig
    models: ModelsConfig
    data_api: DataAPIConfig
    benchmarks_api: BenchmarksAPIConfig
    aws: AWSConfig
    databricks: DatabricksConfig

    @staticmethod
    def load_default_config() -> Dict[str, Any]:
        """Attempt to load the default bundled configuration (config A)."""
        try:
            with resources.open_text("vcp.config", "config.yaml") as f:
                return yaml.safe_load(f) or {}  # `safe_load` can return `None`
        except FileNotFoundError:
            return {}
        except Exception as e:
            raise RuntimeError(f"Bundled configuration is malformed: {e}") from e

    @staticmethod
    def load_user_config(config_path: str = None) -> Dict[str, Any]:
        """Load user configuration from file (config B)."""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path.home() / ".vcp" / "config.yaml"

        if not config_file.exists():
            return {}

        try:
            with open(config_file, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"User configuration is malformed: {e}") from e

    @staticmethod
    def merge_configs(
        default_config: Dict[str, Any], user_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two dictionaries, where user_config overrides default_config."""
        merged = default_config.copy()

        def deep_update(original, updates):
            for key, value in updates.items():
                if (
                    isinstance(value, dict)
                    and key in original
                    and isinstance(original[key], dict)
                ):
                    deep_update(original[key], value)
                else:
                    original[key] = value

        deep_update(merged, user_config)
        return merged

    @classmethod
    def load(cls, config_path: str = None) -> "Config":
        """Load configuration, merging bundled (A) and user config (B)."""
        default_config = cls.load_default_config()
        user_config = cls.load_user_config(config_path)

        final_config = cls.merge_configs(default_config, user_config)

        if not final_config:
            raise RuntimeError("No valid configuration provided.")

        return cls._from_dict(final_config)

    @classmethod
    def _from_dict(cls, data: dict) -> "Config":
        """Create configuration from dictionary."""
        feature_flags = data.get("feature_flags", {})
        aws_data = data.get("aws", {})
        cognito_data = aws_data.get("cognito", {})
        databricks_data = data.get("databricks", {})
        benchmarks_api_data = data.get("benchmarks_api", {})
        models_data = data.get("models", {})
        github_data = models_data.get("github", {})
        data_api_data = data.get("data_api", {})
        data_subcommands_data = feature_flags.get("data_subcommands", {})

        return cls(
            feature_flags=FeatureFlagsConfig(
                data_command=feature_flags.get("data_command", True),
                model_command=feature_flags.get("model_command", True),
                benchmarks_command=feature_flags.get("benchmarks_command", True),
                data_subcommands=DataSubcommandFlags(
                    credentials=data_subcommands_data.get("credentials", True),
                ),
            ),
            models=ModelsConfig(
                base_url=models_data.get(
                    "base_url", "https://models.api.example.com/v1"
                ),
                github=GitHubConfig(
                    contributions_org=github_data.get(
                        "contributions_org", "cz-model-contributions"
                    ),
                    template_repo=github_data.get(
                        "template_repo",
                        "git@github.com:chanzuckerberg/model-template.git",
                    ),
                ),
            ),
            data_api=DataAPIConfig(
                base_url=data_api_data.get(
                    "base_url", "https://data.api.example.com/v1"
                )
            ),
            benchmarks_api=BenchmarksAPIConfig(
                base_url=benchmarks_api_data.get(
                    "base_url", "https://benchmarks.api.example.com/v1"
                ),
                endpoints=BenchmarksAPIEndpointsConfig(
                    **benchmarks_api_data.get("endpoints", {})
                ),
            ),
            aws=AWSConfig(
                region=aws_data.get("region", "us-east-1"),
                cognito=CognitoConfig(
                    user_pool_id=cognito_data.get("user_pool_id", ""),
                    client_id=cognito_data.get("client_id", ""),
                    client_secret=cognito_data.get("client_secret", ""),
                    domain=cognito_data.get("domain", ""),
                    flow=cognito_data.get("flow", "password"),
                ),
            ),
            databricks=DatabricksConfig(
                host=databricks_data.get("host", ""),
                token=databricks_data.get("token", ""),
            ),
        )
