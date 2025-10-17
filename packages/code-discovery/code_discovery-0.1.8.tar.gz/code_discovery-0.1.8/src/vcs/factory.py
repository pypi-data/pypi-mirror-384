"""Factory for creating VCS adapters."""

from typing import Optional
from vcs.base import BaseVCSAdapter
from vcs.github import GitHubAdapter
from vcs.gitlab import GitLabAdapter
from vcs.jenkins import JenkinsAdapter
from vcs.circleci import CircleCIAdapter
from vcs.harness import HarnessAdapter


class VCSAdapterFactory:
    """Factory for creating the appropriate VCS adapter based on the environment."""

    # List of all available adapters in order of precedence
    ADAPTERS = [
        GitHubAdapter,
        GitLabAdapter,
        CircleCIAdapter,
        HarnessAdapter,
        JenkinsAdapter,  # Jenkins last as it has more generic detection
    ]

    @classmethod
    def create_adapter(cls) -> Optional[BaseVCSAdapter]:
        """
        Create and return the appropriate VCS adapter for the current environment.

        Returns:
            Optional[BaseVCSAdapter]: The detected VCS adapter, or None if no platform detected.
        """
        for adapter_class in cls.ADAPTERS:
            adapter = adapter_class()
            if adapter.detect_platform():
                print(f"Detected VCS platform: {adapter.__class__.__name__}")
                return adapter

        print("Warning: No VCS platform detected. Running in local mode.")
        return None

    @classmethod
    def get_adapter_by_name(cls, platform_name: str) -> Optional[BaseVCSAdapter]:
        """
        Get a specific VCS adapter by platform name.

        Args:
            platform_name: Name of the platform (github, gitlab, jenkins, circleci, harness).

        Returns:
            Optional[BaseVCSAdapter]: The requested VCS adapter, or None if not found.
        """
        adapter_map = {
            "github": GitHubAdapter,
            "gitlab": GitLabAdapter,
            "jenkins": JenkinsAdapter,
            "circleci": CircleCIAdapter,
            "harness": HarnessAdapter,
        }

        adapter_class = adapter_map.get(platform_name.lower())
        if adapter_class:
            return adapter_class()
        return None

