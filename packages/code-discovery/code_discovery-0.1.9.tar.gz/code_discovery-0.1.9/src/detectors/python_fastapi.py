"""FastAPI framework detector."""

from pathlib import Path
from typing import List
from detectors.base import BaseDetector
from core.models import FrameworkType


class FastAPIDetector(BaseDetector):
    """Detector for FastAPI applications."""

    def detect(self) -> bool:
        """Detect if FastAPI is present in the repository."""
        indicators = [
            # Check dependency files
            self._check_requirements(),
            self._check_pyproject(),
            self._check_pipfile(),
            # Check for FastAPI imports in source files
            self._check_fastapi_imports(),
        ]

        return any(indicators)

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.FASTAPI

    def get_source_paths(self) -> List[Path]:
        """Get paths to Python source files."""
        source_paths = []

        # Common Python source locations
        common_paths = [
            "app",
            "src",
            "api",
            "main.py",
            "app.py",
        ]

        for path in common_paths:
            full_path = self.repo_path / path
            if full_path.exists():
                source_paths.append(full_path)

        # If no common paths found, search for Python files
        if not source_paths:
            py_files = self.find_files("*.py", max_depth=8)
            # Get unique parent directories
            source_paths = list(set(f.parent for f in py_files))

        return source_paths

    def _check_requirements(self) -> bool:
        """Check for FastAPI in requirements files."""
        req_files = [
            "requirements.txt",
            "requirements/base.txt",
            "requirements/production.txt",
            "requirements/dev.txt",
        ]

        for req_file in req_files:
            if self.check_dependency(req_file, "fastapi"):
                return True

        return False

    def _check_pyproject(self) -> bool:
        """Check for FastAPI in pyproject.toml."""
        if self.check_dependency("pyproject.toml", "fastapi"):
            return True
        return False

    def _check_pipfile(self) -> bool:
        """Check for FastAPI in Pipfile."""
        if self.check_dependency("Pipfile", "fastapi"):
            return True
        return False

    def _check_fastapi_imports(self) -> bool:
        """Check for FastAPI imports in Python source files."""
        py_files = self.find_files("*.py", max_depth=8)

        fastapi_imports = [
            "from fastapi import",
            "import fastapi",
            "FastAPI(",
        ]

        for py_file in py_files[:50]:  # Limit for performance
            content = self.read_file(py_file)
            if content:
                for import_stmt in fastapi_imports:
                    if import_stmt in content:
                        return True

        return False

