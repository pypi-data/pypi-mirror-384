"""ASP.NET Core framework detector."""

from pathlib import Path
from typing import List
from detectors.base import BaseDetector
from core.models import FrameworkType


class DotNetDetector(BaseDetector):
    """Detector for ASP.NET Core applications."""

    def detect(self) -> bool:
        """Detect if ASP.NET Core is present in the repository."""
        indicators = [
            # Check for .NET project files
            self._check_csproj_files(),
            # Check for ASP.NET Core specific files
            self._check_aspnet_files(),
            # Check for ASP.NET Core code patterns
            self._check_aspnet_code(),
        ]

        return any(indicators)

    def get_framework_type(self) -> FrameworkType:
        """Get the framework type."""
        return FrameworkType.ASPNET_CORE

    def get_source_paths(self) -> List[Path]:
        """Get paths to C# source files."""
        source_paths = []

        # Find .csproj files and get their directories
        csproj_files = self.find_files("*.csproj", max_depth=8)
        for csproj in csproj_files:
            source_paths.append(csproj.parent)

        # If no project files found, search for C# files
        if not source_paths:
            cs_files = self.find_files("*.cs", max_depth=8)
            # Get unique parent directories
            source_paths = list(set(f.parent for f in cs_files))

        return source_paths

    def _check_csproj_files(self) -> bool:
        """Check for ASP.NET Core in .csproj files."""
        csproj_files = self.find_files("*.csproj", max_depth=8)

        aspnet_packages = [
            "Microsoft.AspNetCore",
            "Microsoft.AspNetCore.Mvc",
            "Microsoft.AspNetCore.App",
            "Microsoft.NET.Sdk.Web",
        ]

        for csproj in csproj_files:
            content = self.read_file(csproj)
            if content:
                for package in aspnet_packages:
                    if package in content:
                        return True

        return False

    def _check_aspnet_files(self) -> bool:
        """Check for ASP.NET Core specific files."""
        aspnet_files = [
            "Program.cs",
            "Startup.cs",
            "appsettings.json",
            "appsettings.Development.json",
        ]

        for file_name in aspnet_files:
            files = self.find_files(file_name, max_depth=8)
            for file in files:
                content = self.read_file(file)
                if content and any(
                    keyword in content
                    for keyword in [
                        "WebApplication",
                        "UseRouting",
                        "UseEndpoints",
                        "AddControllers",
                        "MapControllers",
                    ]
                ):
                    return True

        return False

    def _check_aspnet_code(self) -> bool:
        """Check for ASP.NET Core code patterns in C# files."""
        cs_files = self.find_files("*.cs", max_depth=8)

        aspnet_patterns = [
            "[ApiController]",
            "[Route(",
            "[HttpGet",
            "[HttpPost",
            "[HttpPut",
            "[HttpDelete",
            "ControllerBase",
            "Controller",
        ]

        for cs_file in cs_files[:50]:  # Limit for performance
            content = self.read_file(cs_file)
            if content:
                for pattern in aspnet_patterns:
                    if pattern in content:
                        return True

        return False

