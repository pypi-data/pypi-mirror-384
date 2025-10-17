"""Harness CI adapter implementation."""

import os
import subprocess
from typing import Dict, Optional
from vcs.base import BaseVCSAdapter
from core.models import VCSContext


class HarnessAdapter(BaseVCSAdapter):
    """Adapter for Harness CI."""

    def detect_platform(self) -> bool:
        """Detect if running on Harness."""
        return os.getenv("HARNESS_BUILD_ID") is not None or os.getenv("DRONE_BUILD_NUMBER") is not None

    def get_context(self) -> VCSContext:
        """Get Harness context."""
        if self._context is None:
            # Harness uses DRONE_ prefixed variables (based on Drone CI)
            self._context = VCSContext(
                platform="harness",
                repository_url=self._get_repo_url(),
                repository_path=self.get_repository_path(),
                branch=self._get_branch_name(),
                commit_sha=self._get_commit_sha(),
                event_type=self._get_event_type(),
                environment_vars=self.get_environment_variables(),
            )
        return self._context

    def get_repository_path(self) -> str:
        """Get the repository path from Harness workspace."""
        # Harness/Drone uses DRONE_WORKSPACE or defaults to current directory
        return os.getenv("DRONE_WORKSPACE", os.getenv("HARNESS_WORKSPACE", os.getcwd()))

    def commit_and_push_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: Optional[str] = None,
    ) -> bool:
        """Commit and push file using Harness."""
        try:
            repo_path = self.get_repository_path()
            full_file_path = os.path.join(repo_path, file_path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

            # Write file
            with open(full_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Configure git
            self._configure_git()

            # Git add
            subprocess.run(
                ["git", "add", file_path],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            # Git commit
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            # Git push
            push_branch = branch or self._get_branch_name()
            subprocess.run(
                ["git", "push", "origin", push_branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            return True
        except Exception as e:
            print(f"Error committing file in Harness: {e}")
            return False

    def create_pull_request(
        self,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
    ) -> Optional[str]:
        """Create a pull request using the appropriate VCS CLI."""
        try:
            repo_url = self._get_repo_url()
            
            if "github.com" in repo_url:
                # Use GitHub CLI
                result = subprocess.run(
                    [
                        "gh",
                        "pr",
                        "create",
                        "--title",
                        title,
                        "--body",
                        body,
                        "--base",
                        target_branch,
                        "--head",
                        source_branch,
                    ],
                    cwd=self.get_repository_path(),
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
                    
            elif "gitlab" in repo_url:
                # Use GitLab CLI
                result = subprocess.run(
                    [
                        "glab",
                        "mr",
                        "create",
                        "--title",
                        title,
                        "--description",
                        body,
                        "--source-branch",
                        source_branch,
                        "--target-branch",
                        target_branch,
                    ],
                    cwd=self.get_repository_path(),
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
                    
            return None
        except Exception as e:
            print(f"Error creating PR from Harness: {e}")
            return None

    def get_environment_variables(self) -> Dict[str, str]:
        """Get Harness environment variables."""
        harness_vars = {}
        for key, value in os.environ.items():
            if key.startswith("HARNESS_") or key.startswith("DRONE_"):
                harness_vars[key] = value
        return harness_vars

    def _get_repo_url(self) -> str:
        """Get repository URL."""
        return (
            os.getenv("DRONE_REPO_LINK")
            or os.getenv("DRONE_GIT_HTTP_URL")
            or os.getenv("HARNESS_REPO_URL")
            or ""
        )

    def _get_branch_name(self) -> str:
        """Get current branch name."""
        return (
            os.getenv("DRONE_BRANCH")
            or os.getenv("DRONE_SOURCE_BRANCH")
            or os.getenv("HARNESS_BRANCH")
            or "main"
        )

    def _get_commit_sha(self) -> Optional[str]:
        """Get commit SHA."""
        return os.getenv("DRONE_COMMIT_SHA") or os.getenv("HARNESS_COMMIT_SHA")

    def _get_event_type(self) -> str:
        """Determine the event type that triggered the build."""
        event = os.getenv("DRONE_BUILD_EVENT") or os.getenv("HARNESS_BUILD_EVENT")
        if event:
            return event
        
        # Fallback logic
        if os.getenv("DRONE_PULL_REQUEST"):
            return "pull_request"
        elif os.getenv("DRONE_TAG"):
            return "tag"
        return "push"

    def _configure_git(self):
        """Configure git for commits."""
        repo_path = self.get_repository_path()

        # Set git user from Harness/Drone environment
        user_name = (
            os.getenv("DRONE_COMMIT_AUTHOR")
            or os.getenv("HARNESS_COMMIT_AUTHOR")
            or "harness-ci"
        )
        user_email = (
            os.getenv("DRONE_COMMIT_AUTHOR_EMAIL")
            or os.getenv("HARNESS_COMMIT_AUTHOR_EMAIL")
            or "harness-ci@harness.io"
        )

        subprocess.run(
            ["git", "config", "user.name", user_name],
            cwd=repo_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", user_email],
            cwd=repo_path,
            capture_output=True,
        )

