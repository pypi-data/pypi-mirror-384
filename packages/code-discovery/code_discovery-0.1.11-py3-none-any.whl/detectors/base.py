"""Base class for framework detectors."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from core.models import FrameworkType


class BaseDetector(ABC):
    """Abstract base class for framework detectors."""

    def __init__(self, repo_path: str):
        """
        Initialize the detector.

        Args:
            repo_path: Path to the repository root.
        """
        self.repo_path = Path(repo_path)

    @abstractmethod
    def detect(self) -> bool:
        """
        Detect if this framework is present in the repository.

        Returns:
            bool: True if framework is detected, False otherwise.
        """
        pass

    @abstractmethod
    def get_framework_type(self) -> FrameworkType:
        """
        Get the framework type.

        Returns:
            FrameworkType: The type of framework this detector handles.
        """
        pass

    @abstractmethod
    def get_source_paths(self) -> List[Path]:
        """
        Get paths to source files that should be analyzed.

        Returns:
            List[Path]: List of paths to source files or directories.
        """
        pass

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a file exists in the repository.

        Args:
            relative_path: Path relative to repository root.

        Returns:
            bool: True if file exists, False otherwise.
        """
        return (self.repo_path / relative_path).exists()

    def find_files(self, pattern: str, max_depth: int = 10) -> List[Path]:
        """
        Find files matching a pattern in the repository.

        Args:
            pattern: Glob pattern to match files.
            max_depth: Maximum directory depth to search.

        Returns:
            List[Path]: List of matching file paths.
        """
        results = []
        try:
            for path in self.repo_path.rglob(pattern):
                # Calculate depth
                depth = len(path.relative_to(self.repo_path).parts)
                if depth <= max_depth and path.is_file():
                    results.append(path)
        except Exception as e:
            print(f"Error searching for files with pattern {pattern}: {e}")
        return results

    def read_file(self, file_path: Path) -> Optional[str]:
        """
        Read file content.

        Args:
            file_path: Path to the file.

        Returns:
            Optional[str]: File content, or None if error.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def check_dependency(self, dependency_file: str, dependency_name: str) -> bool:
        """
        Check if a dependency is present in a dependency file.

        Args:
            dependency_file: Path to dependency file (relative to repo root).
            dependency_name: Name of the dependency to check.

        Returns:
            bool: True if dependency is found, False otherwise.
        """
        file_path = self.repo_path / dependency_file
        if not file_path.exists():
            return False

        content = self.read_file(file_path)
        if content:
            return dependency_name.lower() in content.lower()
        return False

