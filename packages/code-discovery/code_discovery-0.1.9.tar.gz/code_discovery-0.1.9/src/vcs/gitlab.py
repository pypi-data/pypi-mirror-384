"""GitLab CI adapter implementation."""

import os
import subprocess
from typing import Dict, Optional
from vcs.base import BaseVCSAdapter
from core.models import VCSContext


class GitLabAdapter(BaseVCSAdapter):
    """Adapter for GitLab CI."""

    def detect_platform(self) -> bool:
        """Detect if running on GitLab CI."""
        return os.getenv("GITLAB_CI") == "true"

    def get_context(self) -> VCSContext:
        """Get GitLab CI context."""
        if self._context is None:
            self._context = VCSContext(
                platform="gitlab",
                repository_url=os.getenv("CI_PROJECT_URL", ""),
                repository_path=self.get_repository_path(),
                branch=os.getenv("CI_COMMIT_BRANCH", os.getenv("CI_COMMIT_REF_NAME", "")),
                commit_sha=os.getenv("CI_COMMIT_SHA"),
                event_type=os.getenv("CI_PIPELINE_SOURCE"),
                environment_vars=self.get_environment_variables(),
            )
        return self._context

    def get_repository_path(self) -> str:
        """Get the repository path from GitLab CI."""
        return os.getenv("CI_PROJECT_DIR", os.getcwd())

    def commit_and_push_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: Optional[str] = None,
    ) -> bool:
        """Commit and push file to GitLab."""
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
            
            # Use CI/CD token for authentication
            self._setup_git_credentials()
            
            subprocess.run(
                ["git", "push", "origin", push_branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            return True
        except Exception as e:
            print(f"Error committing file to GitLab: {e}")
            return False

    def create_pull_request(
        self,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
    ) -> Optional[str]:
        """Create a merge request on GitLab using glab CLI or API."""
        try:
            # Try using GitLab CLI
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
            print(f"Error creating GitLab MR: {e}")
            return None

    def get_environment_variables(self) -> Dict[str, str]:
        """Get GitLab CI environment variables."""
        gitlab_vars = {}
        for key, value in os.environ.items():
            if key.startswith("CI_") or key.startswith("GITLAB_"):
                gitlab_vars[key] = value
        return gitlab_vars

    def _get_branch_name(self) -> str:
        """Get current branch name."""
        return os.getenv("CI_COMMIT_BRANCH", os.getenv("CI_COMMIT_REF_NAME", "main"))

    def _configure_git(self):
        """Configure git for commits."""
        repo_path = self.get_repository_path()

        # Set git user
        user_name = os.getenv("GITLAB_USER_NAME", "gitlab-ci")
        user_email = os.getenv("GITLAB_USER_EMAIL", "gitlab-ci@gitlab.com")

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

    def _setup_git_credentials(self):
        """Setup git credentials for GitLab CI."""
        ci_token = os.getenv("CI_JOB_TOKEN")
        ci_server = os.getenv("CI_SERVER_HOST", "gitlab.com")
        
        if ci_token:
            # Configure git to use the CI token
            subprocess.run(
                [
                    "git",
                    "config",
                    "--global",
                    f"url.https://gitlab-ci-token:{ci_token}@{ci_server}/.insteadOf",
                    f"https://{ci_server}/",
                ],
                capture_output=True,
            )

