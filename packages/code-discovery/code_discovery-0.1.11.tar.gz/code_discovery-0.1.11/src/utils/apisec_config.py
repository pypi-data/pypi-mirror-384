"""API Security configuration management for .apisec files."""

import os
from pathlib import Path
from typing import Dict, Optional, Any
from configparser import ConfigParser


class APISecConfig:
    """Configuration manager for .apisec files (similar to .pypirc)."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize APISec configuration.

        Args:
            config_path: Path to .apisec file. If None, searches in standard locations.
        """
        self.config_path = config_path or self._find_apisec_file()
        self.config = self._load_config()

    def _find_apisec_file(self) -> Optional[str]:
        """
        Find .apisec file in standard locations.

        Returns:
            Path to .apisec file if found, None otherwise.
        """
        search_paths = [
            # Project root
            ".apisec",
            # Home directory
            os.path.expanduser("~/.apisec"),
            # Current working directory
            os.path.join(os.getcwd(), ".apisec"),
        ]

        for path in search_paths:
            if Path(path).exists():
                return path

        return None

    def _load_config(self) -> ConfigParser:
        """Load configuration from .apisec file."""
        config = ConfigParser()
        
        if self.config_path and Path(self.config_path).exists():
            try:
                config.read(self.config_path)
                print(f"Loaded API security configuration from {self.config_path}")
            except Exception as e:
                print(f"Warning: Error loading .apisec file {self.config_path}: {e}")
        else:
            print("No .apisec file found. Using environment variables for API configuration.")

        return config

    def get_endpoint(self, service: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get endpoint URL for a service.

        Args:
            service: Service name (e.g., 'api-discovery', 'api-security').
            default: Default value if not found.

        Returns:
            Endpoint URL or default value.
        """
        if self.config.has_section(service):
            return self.config.get(service, "endpoint", fallback=default)
        return default

    def get_token(self, service: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get authentication token for a service.

        Args:
            service: Service name (e.g., 'api-discovery', 'api-security').
            default: Default value if not found.

        Returns:
            Authentication token or default value.
        """
        if self.config.has_section(service):
            return self.config.get(service, "token", fallback=default)
        return default

    def get_service_config(self, service: str) -> Dict[str, str]:
        """
        Get complete configuration for a service.

        Args:
            service: Service name.

        Returns:
            Dictionary with service configuration.
        """
        if not self.config.has_section(service):
            return {}

        return dict(self.config.items(service))

    def list_services(self) -> list:
        """
        List all configured services.

        Returns:
            List of service names.
        """
        return self.config.sections()

    def has_service(self, service: str) -> bool:
        """
        Check if a service is configured.

        Args:
            service: Service name.

        Returns:
            True if service is configured, False otherwise.
        """
        return self.config.has_section(service)

    def get_primary_config(self) -> Dict[str, Optional[str]]:
        """
        Get primary API Discovery configuration.

        Returns:
            Dictionary with endpoint and token for primary service.
        """
        # Look for api-discovery service
        if self.has_service("api-discovery"):
            return {
                "endpoint": self.get_endpoint("api-discovery"),
                "token": self.get_token("api-discovery"),
                "service": "api-discovery",
            }

        return {
            "endpoint": None,
            "token": None,
            "service": None,
        }

    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the configuration and return status.

        Returns:
            Dictionary with validation results.
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "services": {},
        }

        if not self.config_path:
            validation["warnings"].append("No .apisec file found")
            return validation

        for service in self.list_services():
            service_config = self.get_service_config(service)
            service_validation = {
                "endpoint": bool(service_config.get("endpoint")),
                "token": bool(service_config.get("token")),
            }

            if not service_validation["endpoint"]:
                validation["errors"].append(f"Service '{service}' missing endpoint")
                validation["valid"] = False

            if not service_validation["token"]:
                validation["warnings"].append(f"Service '{service}' missing token")

            validation["services"][service] = service_validation

        return validation

    @staticmethod
    def create_example_file(path: str = ".apisec") -> bool:
        """
        Create an example .apisec file.

        Args:
            path: Path where to create the example file.

        Returns:
            True if successful, False otherwise.
        """
        example_content = """# Code Discovery API Security Configuration
# This file stores authentication token and API endpoint for external service
# Place this file in your home directory (~/.apisec) or project root (.apisec)

[api-discovery]
endpoint = https://api.your-service.com/v1/discovery
token = your-api-discovery-token-here
"""

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(example_content)
            print(f"Created example .apisec file at {path}")
            return True
        except Exception as e:
            print(f"Error creating example .apisec file: {e}")
            return False
