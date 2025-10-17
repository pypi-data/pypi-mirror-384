"""GitHub VCS adapter implementation."""

import os
import subprocess
from typing import Dict, Optional
from vcs.base import BaseVCSAdapter
from core.models import VCSContext


class GitHubAdapter(BaseVCSAdapter):
    """Adapter for GitHub Actions."""

    def detect_platform(self) -> bool:
        """Detect if running on GitHub Actions."""
        return os.getenv("GITHUB_ACTIONS") == "true"

    def get_context(self) -> VCSContext:
        """Get GitHub Actions context."""
        if self._context is None:
            self._context = VCSContext(
                platform="github",
                repository_url=os.getenv("GITHUB_SERVER_URL", "https://github.com")
                + "/"
                + os.getenv("GITHUB_REPOSITORY", ""),
                repository_path=self.get_repository_path(),
                branch=self._get_branch_name(),
                commit_sha=os.getenv("GITHUB_SHA"),
                event_type=os.getenv("GITHUB_EVENT_NAME"),
                environment_vars=self.get_environment_variables(),
            )
        return self._context

    def get_repository_path(self) -> str:
        """Get the repository path from GitHub workspace."""
        return os.getenv("GITHUB_WORKSPACE", os.getcwd())

    def commit_and_push_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: Optional[str] = None,
    ) -> bool:
        """Commit and push file to GitHub."""
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
            print(f"Error committing file to GitHub: {e}")
            return False

    def create_pull_request(
        self,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
    ) -> Optional[str]:
        """Create a pull request on GitHub using gh CLI or API."""
        try:
            # Try using GitHub CLI first
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
                # Extract PR URL from output
                return result.stdout.strip()
            return None
        except Exception as e:
            print(f"Error creating GitHub PR: {e}")
            return None

    def get_environment_variables(self) -> Dict[str, str]:
        """Get GitHub Actions environment variables."""
        github_vars = {}
        for key, value in os.environ.items():
            if key.startswith("GITHUB_") or key.startswith("RUNNER_"):
                github_vars[key] = value
        return github_vars

    def _get_branch_name(self) -> str:
        """Extract branch name from GitHub ref."""
        ref = os.getenv("GITHUB_REF", "")
        if ref.startswith("refs/heads/"):
            return ref.replace("refs/heads/", "")
        return "main"

    def _configure_git(self):
        """Configure git for commits."""
        repo_path = self.get_repository_path()

        # Set git user
        actor = os.getenv("GITHUB_ACTOR", "github-actions[bot]")
        email = f"{actor}@users.noreply.github.com"

        subprocess.run(
            ["git", "config", "user.name", actor],
            cwd=repo_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", email],
            cwd=repo_path,
            capture_output=True,
        )

