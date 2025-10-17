"""CircleCI adapter implementation."""

import os
import subprocess
from typing import Dict, Optional
from vcs.base import BaseVCSAdapter
from core.models import VCSContext


class CircleCIAdapter(BaseVCSAdapter):
    """Adapter for CircleCI."""

    def detect_platform(self) -> bool:
        """Detect if running on CircleCI."""
        return os.getenv("CIRCLECI") == "true"

    def get_context(self) -> VCSContext:
        """Get CircleCI context."""
        if self._context is None:
            self._context = VCSContext(
                platform="circleci",
                repository_url=os.getenv("CIRCLE_REPOSITORY_URL", ""),
                repository_path=self.get_repository_path(),
                branch=os.getenv("CIRCLE_BRANCH", ""),
                commit_sha=os.getenv("CIRCLE_SHA1"),
                event_type=self._get_event_type(),
                environment_vars=self.get_environment_variables(),
            )
        return self._context

    def get_repository_path(self) -> str:
        """Get the repository path from CircleCI."""
        return os.getenv("CIRCLE_WORKING_DIRECTORY", os.getcwd())

    def commit_and_push_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: Optional[str] = None,
    ) -> bool:
        """Commit and push file using CircleCI."""
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
            push_branch = branch or os.getenv("CIRCLE_BRANCH", "main")
            subprocess.run(
                ["git", "push", "origin", push_branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            return True
        except Exception as e:
            print(f"Error committing file in CircleCI: {e}")
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
            repo_url = os.getenv("CIRCLE_REPOSITORY_URL", "")
            
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
            print(f"Error creating PR from CircleCI: {e}")
            return None

    def get_environment_variables(self) -> Dict[str, str]:
        """Get CircleCI environment variables."""
        circle_vars = {}
        for key, value in os.environ.items():
            if key.startswith("CIRCLE_"):
                circle_vars[key] = value
        return circle_vars

    def _get_event_type(self) -> str:
        """Determine the event type that triggered the build."""
        if os.getenv("CIRCLE_PULL_REQUEST"):
            return "pull_request"
        elif os.getenv("CIRCLE_TAG"):
            return "tag"
        return "push"

    def _configure_git(self):
        """Configure git for commits."""
        repo_path = self.get_repository_path()

        # Set git user from CircleCI environment
        user_name = os.getenv("CIRCLE_USERNAME", "circleci")
        user_email = f"{user_name}@circleci.com"

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

