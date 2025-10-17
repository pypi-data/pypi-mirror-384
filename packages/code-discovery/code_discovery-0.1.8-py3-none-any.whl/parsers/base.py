"""Base class for API parsers."""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from core.models import APIEndpoint, DiscoveryResult, FrameworkType


class BaseParser(ABC):
    """Abstract base class for API parsers."""

    def __init__(self, source_paths: List[Path], repo_path: Path):
        """
        Initialize the parser.

        Args:
            source_paths: List of paths to source files or directories.
            repo_path: Path to the repository root.
        """
        self.source_paths = source_paths
        self.repo_path = repo_path

    @abstractmethod
    def parse(self) -> DiscoveryResult:
        """
        Parse source files and extract API endpoint information.

        Returns:
            DiscoveryResult: The discovered API information.
        """
        pass

    @abstractmethod
    def get_framework_type(self) -> FrameworkType:
        """
        Get the framework type.

        Returns:
            FrameworkType: The type of framework this parser handles.
        """
        pass

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

    def find_files(self, pattern: str, search_paths: Optional[List[Path]] = None) -> List[Path]:
        """
        Find files matching a pattern.

        Args:
            pattern: Glob pattern to match files.
            search_paths: Paths to search in (defaults to self.source_paths).

        Returns:
            List[Path]: List of matching file paths.
        """
        if search_paths is None:
            search_paths = self.source_paths

        results = []
        for search_path in search_paths:
            if search_path.is_file():
                if search_path.match(pattern):
                    results.append(search_path)
            elif search_path.is_dir():
                results.extend(search_path.rglob(pattern))

        return results

    def extract_path_variables(self, path: str) -> List[str]:
        """
        Extract path variables from a route path.

        Args:
            path: Route path string.

        Returns:
            List[str]: List of path variable names.
        """
        # Match {variable}, :variable, <variable>, etc.
        patterns = [
            r'\{(\w+)\}',  # {id}
            r':(\w+)',      # :id
            r'<(\w+)>',     # <id>
            r'<\w+:(\w+)>', # <int:id>
        ]

        variables = []
        for pattern in patterns:
            variables.extend(re.findall(pattern, path))

        return variables

    def normalize_path(self, path: str) -> str:
        """
        Normalize a path to OpenAPI format.

        Args:
            path: Route path string.

        Returns:
            str: Normalized path with {variable} format.
        """
        # Convert :variable to {variable}
        path = re.sub(r':(\w+)', r'{\1}', path)
        
        # Convert <variable> to {variable}
        path = re.sub(r'<(\w+)>', r'{\1}', path)
        
        # Convert <type:variable> to {variable}
        path = re.sub(r'<\w+:(\w+)>', r'{\1}', path)
        
        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path

        return path

    def get_relative_path(self, file_path: Path) -> str:
        """
        Get relative path from repository root.

        Args:
            file_path: Absolute file path.

        Returns:
            str: Relative path from repository root.
        """
        try:
            return str(file_path.relative_to(self.repo_path))
        except ValueError:
            return str(file_path)

