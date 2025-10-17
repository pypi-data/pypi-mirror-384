"""Base class for VCS adapters."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from core.models import VCSContext


class BaseVCSAdapter(ABC):
    """Abstract base class for VCS platform adapters."""

    def __init__(self):
        """Initialize the VCS adapter."""
        self._context: Optional[VCSContext] = None

    @abstractmethod
    def detect_platform(self) -> bool:
        """
        Detect if running on this VCS platform.

        Returns:
            bool: True if this is the correct platform, False otherwise.
        """
        pass

    @abstractmethod
    def get_context(self) -> VCSContext:
        """
        Get VCS context information.

        Returns:
            VCSContext: Context information from the VCS platform.
        """
        pass

    @abstractmethod
    def get_repository_path(self) -> str:
        """
        Get the local path to the repository.

        Returns:
            str: Absolute path to the repository.
        """
        pass

    @abstractmethod
    def commit_and_push_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: Optional[str] = None,
    ) -> bool:
        """
        Commit and push a file to the repository.

        Args:
            file_path: Path to the file relative to repository root.
            content: Content to write to the file.
            commit_message: Commit message.
            branch: Branch to commit to (defaults to current branch).

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def create_pull_request(
        self,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
    ) -> Optional[str]:
        """
        Create a pull request.

        Args:
            title: PR title.
            body: PR description.
            source_branch: Source branch name.
            target_branch: Target branch name.

        Returns:
            Optional[str]: URL of the created PR, or None if failed.
        """
        pass

    @abstractmethod
    def get_environment_variables(self) -> Dict[str, str]:
        """
        Get relevant environment variables from the VCS platform.

        Returns:
            Dict[str, str]: Dictionary of environment variables.
        """
        pass

    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Read file content from the repository.

        Args:
            file_path: Path to the file relative to repository root.

        Returns:
            Optional[str]: File content, or None if file doesn't exist.
        """
        import os

        full_path = os.path.join(self.get_repository_path(), file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

