"""Spring Boot framework detector."""

from pathlib import Path
from typing import List
from detectors.base import BaseDetector
from core.models import FrameworkType


class SpringBootDetector(BaseDetector):
    """Detector for Spring Boot applications."""

    def detect(self) -> bool:
        """Detect if Spring Boot is present in the repository."""
        # Check for common Spring Boot indicators
        indicators = [
            # Maven
            self._check_maven_spring_boot(),
            # Gradle
            self._check_gradle_spring_boot(),
            # Spring Boot annotations in source files
            self._check_spring_annotations(),
        ]

        return any(indicators)

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.SPRING_BOOT

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

    def _check_maven_spring_boot(self) -> bool:
        """Check for Spring Boot in Maven configuration."""
        pom_files = ["pom.xml"]

        for pom in pom_files:
            if self.check_dependency(pom, "spring-boot-starter-web"):
                return True
            if self.check_dependency(pom, "spring-boot-starter"):
                return True

        return False

    def _check_gradle_spring_boot(self) -> bool:
        """Check for Spring Boot in Gradle configuration."""
        gradle_files = [
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle",
            "settings.gradle.kts",
        ]

        for gradle_file in gradle_files:
            if self.check_dependency(gradle_file, "spring-boot-starter-web"):
                return True
            if self.check_dependency(gradle_file, "org.springframework.boot"):
                return True

        return False

    def _check_spring_annotations(self) -> bool:
        """Check for Spring Boot annotations in source files."""
        # Look for files with Spring Boot annotations
        java_files = self.find_files("*.java", max_depth=8)

        spring_annotations = [
            "@SpringBootApplication",
            "@RestController",
            "@Controller",
            "@RequestMapping",
        ]

        for java_file in java_files[:50]:  # Limit to first 50 files for performance
            content = self.read_file(java_file)
            if content:
                for annotation in spring_annotations:
                    if annotation in content:
                        return True

        return False

