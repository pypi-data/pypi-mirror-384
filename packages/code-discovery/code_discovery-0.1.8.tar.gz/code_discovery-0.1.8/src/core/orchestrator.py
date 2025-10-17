"""Main orchestrator for API discovery workflow."""

from pathlib import Path
from typing import List, Optional, Dict, Any
from core.models import DiscoveryResult, FrameworkType, VCSContext
from vcs.base import BaseVCSAdapter
from vcs.factory import VCSAdapterFactory
from detectors.base import BaseDetector
from detectors.java_spring import SpringBootDetector
from detectors.java_micronaut import MicronautDetector
from detectors.python_fastapi import FastAPIDetector
from detectors.python_flask import FlaskDetector
from detectors.dotnet import DotNetDetector
from parsers.base import BaseParser
from parsers.java_spring_parser import SpringBootParser
from parsers.java_micronaut_parser import MicronautParser
from parsers.fastapi_parser import FastAPIParser
from parsers.flask_parser import FlaskParser
from parsers.dotnet_parser import DotNetParser
from generators.openapi_generator import OpenAPIGenerator
from utils.config import Config
from utils.api_client import APIClient


class Orchestrator:
    """Main orchestrator for the API discovery workflow."""

    # Mapping of framework types to detector and parser classes
    FRAMEWORK_HANDLERS = {
        FrameworkType.SPRING_BOOT: (SpringBootDetector, SpringBootParser),
        FrameworkType.MICRONAUT: (MicronautDetector, MicronautParser),
        FrameworkType.FASTAPI: (FastAPIDetector, FastAPIParser),
        FrameworkType.FLASK: (FlaskDetector, FlaskParser),
        FrameworkType.ASPNET_CORE: (DotNetDetector, DotNetParser),
    }

    def __init__(
        self,
        repo_path: Optional[str] = None,
        config_path: Optional[str] = None,
        vcs_adapter: Optional[BaseVCSAdapter] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            repo_path: Path to the repository (optional, auto-detected from VCS).
            config_path: Path to configuration file (optional).
            vcs_adapter: VCS adapter instance (optional, auto-detected).
        """
        self.config = Config(config_path)
        self.vcs_adapter = vcs_adapter or VCSAdapterFactory.create_adapter()
        
        # Determine repository path
        if repo_path:
            self.repo_path = Path(repo_path)
        elif self.vcs_adapter:
            self.repo_path = Path(self.vcs_adapter.get_repository_path())
        else:
            self.repo_path = Path.cwd()

        print(f"Repository path: {self.repo_path}")

    def _is_dry_run(self) -> bool:
        """
        Check if the orchestrator is running in dry-run mode.
        
        Returns:
            bool: True if in dry-run mode, False otherwise.
        """
        # Check if auto_commit is disabled (indicates dry-run mode)
        return not self.config.auto_commit

    def run(self) -> bool:
        """
        Run the complete API discovery workflow.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.config.enabled:
            print("API discovery is disabled in configuration.")
            return False

        print("\n" + "="*60)
        print("Code Discovery - API Discovery System")
        print("="*60 + "\n")

        # Step 1: Detect frameworks
        print("Step 1: Detecting frameworks...")
        detected_frameworks = self._detect_frameworks()

        if not detected_frameworks:
            print("✗ No API frameworks detected in this repository.")
            return False

        print(f"✓ Detected {len(detected_frameworks)} framework(s):")
        for framework in detected_frameworks:
            print(f"  - {framework.value}")

        # Step 2: Parse APIs from detected frameworks
        print("\nStep 2: Parsing API endpoints...")
        all_results = []
        for framework in detected_frameworks:
            result = self._parse_framework(framework)
            if result and result.endpoints:
                all_results.append(result)
                print(f"✓ Found {len(result.endpoints)} endpoint(s) in {framework.value}")

        if not all_results:
            print("✗ No API endpoints found.")
            return False

        # Step 3: Merge results and generate OpenAPI spec
        print("\nStep 3: Generating OpenAPI specification...")
        merged_result = self._merge_results(all_results)
        openapi_spec = self._generate_openapi_spec(merged_result)

        # Step 4: Save OpenAPI spec
        print("\nStep 4: Saving OpenAPI specification...")
        spec_path = self._save_openapi_spec(openapi_spec, merged_result)
        if not spec_path:
            print("✗ Failed to save OpenAPI specification.")
            return False

        print(f"✓ Saved OpenAPI specification to {spec_path}")

        # Step 5: Commit to VCS (if enabled)
        if self.config.auto_commit and self.vcs_adapter:
            print("\nStep 5: Committing to VCS...")
            self._commit_to_vcs(spec_path)

        # Step 6: Notify external API (if not dry run and .apisec is configured)
        if not self._is_dry_run():
            print("\nStep 6: Notifying external API...")
            self._notify_external_api(openapi_spec, merged_result)
        else:
            print("\nStep 6: Skipping external API notification (dry run mode)")

        print("\n" + "="*60)
        print("✓ API Discovery completed successfully!")
        print("="*60 + "\n")

        return True

    def _detect_frameworks(self) -> List[FrameworkType]:
        """Detect frameworks in the repository."""
        detected = []

        # If specific frameworks are configured, only check those
        configured_frameworks = self.config.frameworks
        if configured_frameworks:
            frameworks_to_check = [
                fw for fw in FrameworkType 
                if fw.value in configured_frameworks and fw in self.FRAMEWORK_HANDLERS
            ]
        else:
            # Check all frameworks
            frameworks_to_check = list(self.FRAMEWORK_HANDLERS.keys())

        for framework_type in frameworks_to_check:
            detector_class, _ = self.FRAMEWORK_HANDLERS[framework_type]
            detector = detector_class(str(self.repo_path))

            if detector.detect():
                detected.append(framework_type)

        return detected

    def _parse_framework(self, framework: FrameworkType) -> Optional[DiscoveryResult]:
        """Parse a specific framework for API endpoints."""
        if framework not in self.FRAMEWORK_HANDLERS:
            print(f"Warning: No parser available for {framework.value}")
            return None

        detector_class, parser_class = self.FRAMEWORK_HANDLERS[framework]

        # Get source paths from detector
        detector = detector_class(str(self.repo_path))
        source_paths = detector.get_source_paths()

        if not source_paths:
            print(f"Warning: No source paths found for {framework.value}")
            return None

        # Parse the source files
        parser = parser_class(source_paths, self.repo_path)
        result = parser.parse()

        return result

    def _merge_results(self, results: List[DiscoveryResult]) -> DiscoveryResult:
        """Merge multiple discovery results into one."""
        if len(results) == 1:
            return results[0]

        # Merge all endpoints
        all_endpoints = []
        frameworks = []

        for result in results:
            all_endpoints.extend(result.endpoints)
            frameworks.append(result.framework.value)

        # Create merged result
        merged = DiscoveryResult(
            framework=results[0].framework,  # Use first framework as primary
            endpoints=all_endpoints,
            title=f"Discovered API ({', '.join(frameworks)})",
            description=f"API endpoints discovered from multiple frameworks: {', '.join(frameworks)}",
            metadata={
                "repository_path": str(self.repo_path),
                "frameworks": frameworks,
            }
        )

        return merged

    def _generate_openapi_spec(self, result: DiscoveryResult) -> Dict[str, Any]:
        """Generate OpenAPI specification from discovery result."""
        generator = OpenAPIGenerator(version=self.config.openapi_version)
        return generator.generate(result)

    def _save_openapi_spec(
        self,
        spec: Dict[str, Any],
        result: DiscoveryResult,
    ) -> Optional[str]:
        """Save OpenAPI specification to file."""
        output_path = self.repo_path / self.config.output_path
        output_format = self.config.output_format

        try:
            generator = OpenAPIGenerator(version=self.config.openapi_version)

            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate and write spec
            if output_format == "json":
                content = generator.generate_json(result)
            else:
                content = generator.generate_yaml(result)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            return str(output_path.relative_to(self.repo_path))

        except Exception as e:
            print(f"Error saving OpenAPI spec: {e}")
            return None

    def _commit_to_vcs(self, file_path: str) -> bool:
        """Commit OpenAPI spec to VCS."""
        if not self.vcs_adapter:
            print("Warning: No VCS adapter available. Skipping commit.")
            return False

        try:
            # Read file content
            full_path = self.repo_path / file_path
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Commit and push
            success = self.vcs_adapter.commit_and_push_file(
                file_path=file_path,
                content=content,
                commit_message=self.config.commit_message,
                branch=self.config.commit_branch,
            )

            if success:
                print(f"✓ Committed {file_path} to VCS")

                # Create PR if configured
                if self.config.create_pr:
                    context = self.vcs_adapter.get_context()
                    pr_url = self.vcs_adapter.create_pull_request(
                        title=self.config.pr_title,
                        body=self.config.pr_body,
                        source_branch=context.branch,
                        target_branch="main",
                    )
                    if pr_url:
                        print(f"✓ Created pull request: {pr_url}")

            return success

        except Exception as e:
            print(f"Error committing to VCS: {e}")
            return False

    def _notify_external_api(
        self,
        spec: Dict[str, Any],
        result: DiscoveryResult,
    ) -> bool:
        """Notify external API about discovered APIs."""
        try:
            # Prepare metadata
            metadata = {
                "framework": result.framework.value,
                "endpoint_count": len(result.endpoints),
                "repository_path": str(self.repo_path),
            }

            # Add VCS context if available
            if self.vcs_adapter:
                context = self.vcs_adapter.get_context()
                metadata["vcs"] = {
                    "platform": context.platform,
                    "repository_url": context.repository_url,
                    "branch": context.branch,
                    "commit_sha": context.commit_sha,
                }

            # Try to use .apisec configuration first
            apisec_config = self.config.apisec_config.get_primary_config()
            if apisec_config.get("endpoint") and apisec_config.get("token"):
                print("Using .apisec configuration for external API notification")
                client = APIClient(
                    endpoint=apisec_config["endpoint"],
                    auth_token=apisec_config["token"],
                    timeout=self.config.external_api_timeout,
                )
                
                # Send to external API
                success = client.send_openapi_spec(spec, metadata)
                return success
            else:
                # Check if traditional configuration is available
                if self.config.external_api_endpoint and self.config.external_api_token:
                    print("Using traditional configuration for external API notification")
                    client = APIClient(
                        endpoint=self.config.external_api_endpoint,
                        auth_token=self.config.external_api_token,
                        timeout=self.config.external_api_timeout,
                    )

                    # Send to external API
                    success = client.send_openapi_spec(spec, metadata)
                    return success
                else:
                    print("No external API configuration found. Skipping notification.")
                    print("  To enable external API notifications:")
                    print("  1. Create a .apisec file: code-discovery --create-apisec")
                    print("  2. Add your API endpoint and token to the .apisec file")
                    return True  # Not an error, just no configuration

        except Exception as e:
            print(f"Error notifying external API: {e}")
            return False

