"""Main entry point for Code Discovery."""

import argparse
import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from core.orchestrator import Orchestrator


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Code Discovery - Automatic API Discovery System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in current directory
  code-discovery

  # Run on specific repository
  code-discovery --repo-path /path/to/repo

  # Dry run (don't commit)
  code-discovery --dry-run

  # Use custom config
  code-discovery --config /path/to/config.yml

  # .apisec configuration management
  code-discovery --create-apisec
  code-discovery --validate-apisec
  code-discovery --list-apisec-services
        """,
    )

    parser.add_argument(
        "--repo-path",
        type=str,
        help="Path to the repository to analyze (default: current directory)",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: .codediscovery.yml)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run discovery without committing changes",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output path for OpenAPI spec (overrides config)",
    )

    parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        help="Output format for OpenAPI spec (overrides config)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Code Discovery 0.1.6",
    )

    # .apisec configuration commands
    parser.add_argument(
        "--create-apisec",
        action="store_true",
        help="Create an example .apisec configuration file",
    )

    parser.add_argument(
        "--validate-apisec",
        action="store_true",
        help="Validate .apisec configuration file",
    )

    parser.add_argument(
        "--list-apisec-services",
        action="store_true",
        help="List all configured services in .apisec file",
    )

    args = parser.parse_args()

    try:
        # Handle .apisec configuration commands
        if args.create_apisec:
            from utils.apisec_config import APISecConfig
            success = APISecConfig.create_example_file(".apisec")
            if success:
                print("✓ Created example .apisec file")
                print("Edit the file to add your API endpoints and tokens")
            else:
                print("✗ Failed to create .apisec file")
            sys.exit(0 if success else 1)

        if args.validate_apisec:
            from utils.apisec_config import APISecConfig
            config = APISecConfig()
            primary_config = config.get_primary_config()
            
            if primary_config.get("endpoint") and primary_config.get("token"):
                print("✓ .apisec configuration is valid")
                print(f"  - endpoint: {primary_config['endpoint']}")
                print(f"  - token: {'*' * 10}...")
            else:
                print("✗ .apisec configuration is invalid")
                if not primary_config.get("endpoint"):
                    print("  - Missing endpoint")
                if not primary_config.get("token"):
                    print("  - Missing token")
                sys.exit(1)
            
            sys.exit(0)

        if args.list_apisec_services:
            from utils.apisec_config import APISecConfig
            config = APISecConfig()
            primary_config = config.get_primary_config()
            
            if primary_config.get("endpoint"):
                endpoint = primary_config["endpoint"]
                has_token = bool(primary_config.get("token"))
                token_status = "✓" if has_token else "✗"
                print("Configured service in .apisec:")
                print(f"  - api-discovery: {endpoint} (token: {token_status})")
            else:
                print("No service configured in .apisec file")
                print("Use --create-apisec to create an example configuration")
            
            sys.exit(0)

        # Create orchestrator
        orchestrator = Orchestrator(
            repo_path=args.repo_path,
            config_path=args.config,
        )

        # Override config if CLI args provided
        if args.dry_run:
            orchestrator.config.config["api_discovery"]["vcs"]["auto_commit"] = False
            orchestrator.config.config["api_discovery"]["external_api"]["enabled"] = False

        if args.output:
            orchestrator.config.config["api_discovery"]["openapi"]["output_path"] = args.output

        if args.format:
            orchestrator.config.config["api_discovery"]["openapi"]["output_format"] = args.format

        # Run discovery
        success = orchestrator.run()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

