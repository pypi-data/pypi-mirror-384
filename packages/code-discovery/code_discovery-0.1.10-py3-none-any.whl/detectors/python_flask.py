"""Flask framework detector."""

from pathlib import Path
from typing import List
from detectors.base import BaseDetector
from core.models import FrameworkType


class FlaskDetector(BaseDetector):
    """Detector for Flask applications."""

    def detect(self) -> bool:
        """Detect if Flask is present in the repository."""
        indicators = [
            # Check dependency files
            self._check_requirements(),
            self._check_pyproject(),
            self._check_pipfile(),
            # Check for Flask imports in source files
            self._check_flask_imports(),
        ]

        return any(indicators)

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.FLASK

    def get_source_paths(self) -> List[Path]:
        """Get paths to Python source files."""
        source_paths = []

        # Common Flask source locations
        common_paths = [
            "app",
            "src",
            "api",
            "application",
            "main.py",
            "app.py",
            "wsgi.py",
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
        """Check for Flask in requirements files."""
        req_files = [
            "requirements.txt",
            "requirements/base.txt",
            "requirements/production.txt",
            "requirements/dev.txt",
        ]

        for req_file in req_files:
            if self.check_dependency(req_file, "flask"):
                return True

        return False

    def _check_pyproject(self) -> bool:
        """Check for Flask in pyproject.toml."""
        if self.check_dependency("pyproject.toml", "flask"):
            return True
        return False

    def _check_pipfile(self) -> bool:
        """Check for Flask in Pipfile."""
        if self.check_dependency("Pipfile", "flask"):
            return True
        return False

    def _check_flask_imports(self) -> bool:
        """Check for Flask imports in Python source files."""
        py_files = self.find_files("*.py", max_depth=8)

        flask_imports = [
            "from flask import",
            "import flask",
            "Flask(__name__)",
        ]

        for py_file in py_files[:50]:  # Limit for performance
            content = self.read_file(py_file)
            if content:
                for import_stmt in flask_imports:
                    if import_stmt in content:
                        return True

        return False

