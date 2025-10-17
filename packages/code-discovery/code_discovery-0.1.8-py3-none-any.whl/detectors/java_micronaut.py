"""Micronaut framework detector."""

from pathlib import Path
from typing import List
from detectors.base import BaseDetector
from core.models import FrameworkType


class MicronautDetector(BaseDetector):
    """Detector for Micronaut applications."""

    def detect(self) -> bool:
        """Detect if Micronaut is present in the repository."""
        # Check for common Micronaut indicators
        indicators = [
            # Maven
            self._check_maven_micronaut(),
            # Gradle
            self._check_gradle_micronaut(),
            # Micronaut config files
            self._check_micronaut_config(),
            # Micronaut annotations in source files
            self._check_micronaut_annotations(),
        ]

        return any(indicators)

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.MICRONAUT

    def get_source_paths(self) -> List[Path]:
        """Get paths to Java source files."""
        source_paths = []

        # Common Java source locations
        common_paths = [
            "src/main/java",
            "src/test/java",
        ]

        for path in common_paths:
            full_path = self.repo_path / path
            if full_path.exists():
                source_paths.append(full_path)

        # If no common paths found, search for any Java files
        if not source_paths:
            java_files = self.find_files("*.java", max_depth=8)
            # Get unique parent directories
            source_paths = list(set(f.parent for f in java_files))

        return source_paths

    def _check_maven_micronaut(self) -> bool:
        """Check for Micronaut in Maven configuration."""
        if self.check_dependency("pom.xml", "micronaut-http-server-netty"):
            return True
        if self.check_dependency("pom.xml", "io.micronaut"):
            return True
        return False

    def _check_gradle_micronaut(self) -> bool:
        """Check for Micronaut in Gradle configuration."""
        gradle_files = [
            "build.gradle",
            "build.gradle.kts",
        ]

        for gradle_file in gradle_files:
            if self.check_dependency(gradle_file, "io.micronaut"):
                return True
            if self.check_dependency(gradle_file, "micronaut-http-server-netty"):
                return True

        return False

    def _check_micronaut_config(self) -> bool:
        """Check for Micronaut configuration files."""
        config_files = [
            "src/main/resources/application.yml",
            "src/main/resources/application.yaml",
            "src/main/resources/application.properties",
            "micronaut-cli.yml",
        ]

        for config_file in config_files:
            if self.file_exists(config_file):
                content = self.read_file(self.repo_path / config_file)
                if content and "micronaut" in content.lower():
                    return True

        return False

    def _check_micronaut_annotations(self) -> bool:
        """Check for Micronaut annotations in source files."""
        java_files = self.find_files("*.java", max_depth=8)

        micronaut_annotations = [
            "@Controller",
            "@Get",
            "@Post",
            "@Put",
            "@Delete",
            "io.micronaut",
        ]

        for java_file in java_files[:50]:  # Limit to first 50 files for performance
            content = self.read_file(java_file)
            if content:
                for annotation in micronaut_annotations:
                    if annotation in content:
                        return True

        return False

