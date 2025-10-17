"""Configuration management."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from .apisec_config import APISecConfig


class Config:
    """Configuration manager for Code Discovery."""

    DEFAULT_CONFIG = {
        "api_discovery": {
            "enabled": True,
            "frameworks": [],  # Empty means auto-detect all
            "openapi": {
                "version": "3.0.0",
                "output_path": "openapi-spec.yaml",
                "output_format": "yaml",  # yaml or json
                "include_examples": True,
            },
            "external_api": {
                "enabled": False,
                "endpoint": "",
                "auth_token_env": "API_DISCOVERY_TOKEN",
                "timeout": 30,
            },
            "vcs": {
                "auto_commit": True,
                "commit_message": "chore: update OpenAPI specification",
                "branch": None,  # None means use current branch
                "create_pr": False,
                "pr_title": "Update OpenAPI Specification",
                "pr_body": "Automatically generated OpenAPI specification",
            },
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to configuration file. If None, searches for
                        .codediscovery.yml in current directory.
        """
        self.config = self._load_config(config_path)
        # Initialize APISec configuration for .apisec file support
        self.apisec_config = APISecConfig()

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        # Start with defaults
        config = self.DEFAULT_CONFIG.copy()

        # Try to find config file
        if config_path is None:
            config_path = self._find_config_file()

        # Load and merge config file if found
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        config = self._deep_merge(config, user_config)
                        print(f"Loaded configuration from {config_path}")
            except Exception as e:
                print(f"Warning: Error loading config file {config_path}: {e}")

        return config

    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in standard locations."""
        search_paths = [
            ".codediscovery.yml",
            ".codediscovery.yaml",
            "codediscovery.yml",
            "codediscovery.yaml",
        ]

        for path in search_paths:
            if Path(path).exists():
                return path

        return None

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Args:
            key: Configuration key in dot notation (e.g., "api_discovery.enabled").
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @property
    def enabled(self) -> bool:
        """Check if API discovery is enabled."""
        return self.get("api_discovery.enabled", True)

    @property
    def frameworks(self) -> List[str]:
        """Get list of frameworks to scan for."""
        return self.get("api_discovery.frameworks", [])

    @property
    def openapi_version(self) -> str:
        """Get OpenAPI version."""
        return self.get("api_discovery.openapi.version", "3.0.0")

    @property
    def output_path(self) -> str:
        """Get OpenAPI output path."""
        return self.get("api_discovery.openapi.output_path", "openapi-spec.yaml")

    @property
    def output_format(self) -> str:
        """Get OpenAPI output format (yaml or json)."""
        return self.get("api_discovery.openapi.output_format", "yaml")

    @property
    def include_examples(self) -> bool:
        """Check if examples should be included in OpenAPI spec."""
        return self.get("api_discovery.openapi.include_examples", True)

    @property
    def external_api_enabled(self) -> bool:
        """Check if external API notification is enabled."""
        return self.get("api_discovery.external_api.enabled", False)

    @property
    def external_api_endpoint(self) -> str:
        """Get external API endpoint from .apisec file or configuration."""
        # First try to get from .apisec file
        apisec_config = self.apisec_config.get_primary_config()
        if apisec_config.get("endpoint"):
            return apisec_config["endpoint"]
        
        # Fallback to configuration file
        return self.get("api_discovery.external_api.endpoint", "")

    @property
    def external_api_token(self) -> Optional[str]:
        """Get external API authentication token from .apisec file or environment."""
        # First try to get from .apisec file
        apisec_config = self.apisec_config.get_primary_config()
        if apisec_config.get("token"):
            return apisec_config["token"]
        
        # Fallback to environment variable
        token_env = self.get(
            "api_discovery.external_api.auth_token_env", "API_DISCOVERY_TOKEN"
        )
        return os.getenv(token_env)

    @property
    def external_api_timeout(self) -> int:
        """Get external API request timeout."""
        return self.get("api_discovery.external_api.timeout", 30)

    @property
    def auto_commit(self) -> bool:
        """Check if auto-commit is enabled."""
        return self.get("api_discovery.vcs.auto_commit", True)

    @property
    def commit_message(self) -> str:
        """Get commit message."""
        return self.get(
            "api_discovery.vcs.commit_message",
            "chore: update OpenAPI specification",
        )

    @property
    def commit_branch(self) -> Optional[str]:
        """Get branch to commit to."""
        return self.get("api_discovery.vcs.branch")

    @property
    def create_pr(self) -> bool:
        """Check if PR creation is enabled."""
        return self.get("api_discovery.vcs.create_pr", False)

    @property
    def pr_title(self) -> str:
        """Get PR title."""
        return self.get("api_discovery.vcs.pr_title", "Update OpenAPI Specification")

    @property
    def pr_body(self) -> str:
        """Get PR body."""
        return self.get(
            "api_discovery.vcs.pr_body",
            "Automatically generated OpenAPI specification",
        )

    def get_apisec_service_config(self, service: str) -> Dict[str, str]:
        """
        Get configuration for a specific service from .apisec file.

        Args:
            service: Service name (e.g., 'api-discovery', 'api-security').

        Returns:
            Dictionary with service configuration.
        """
        return self.apisec_config.get_service_config(service)

    def list_apisec_services(self) -> list:
        """
        List all services configured in .apisec file.

        Returns:
            List of service names.
        """
        return self.apisec_config.list_services()

    def validate_apisec_config(self) -> Dict[str, Any]:
        """
        Validate .apisec configuration.

        Returns:
            Dictionary with validation results.
        """
        return self.apisec_config.validate_config()

    def create_apisec_example(self, path: str = ".apisec") -> bool:
        """
        Create an example .apisec file.

        Args:
            path: Path where to create the example file.

        Returns:
            True if successful, False otherwise.
        """
        return APISecConfig.create_example_file(path)

