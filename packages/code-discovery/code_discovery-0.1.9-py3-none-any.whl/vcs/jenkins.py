"""Jenkins adapter implementation."""

import os
import subprocess
from typing import Dict, Optional
from vcs.base import BaseVCSAdapter
from core.models import VCSContext


class JenkinsAdapter(BaseVCSAdapter):
    """Adapter for Jenkins CI."""

    def detect_platform(self) -> bool:
        """Detect if running on Jenkins."""
        return os.getenv("JENKINS_HOME") is not None or os.getenv("HUDSON_HOME") is not None

    def get_context(self) -> VCSContext:
        """Get Jenkins context."""
        if self._context is None:
            # Jenkins uses different variables for different SCM plugins
            git_url = (
                os.getenv("GIT_URL")
                or os.getenv("GIT_URL_1")
                or os.getenv("gitlabSourceRepoHttpUrl")
                or ""
            )

            self._context = VCSContext(
                platform="jenkins",
                repository_url=git_url,
                repository_path=self.get_repository_path(),
                branch=self._get_branch_name(),
                commit_sha=os.getenv("GIT_COMMIT"),
                event_type=self._get_event_type(),
                environment_vars=self.get_environment_variables(),
            )
        return self._context

    def get_repository_path(self) -> str:
        """Get the repository path from Jenkins workspace."""
        return os.getenv("WORKSPACE", os.getcwd())

    def commit_and_push_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: Optional[str] = None,
    ) -> bool:
        """Commit and push file using Jenkins."""
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
            print(f"Error committing file in Jenkins: {e}")
            return False

    def create_pull_request(
        self,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str,
    ) -> Optional[str]:
        """
        Create a pull request. Implementation depends on the underlying VCS.
        
        Note: Jenkins itself doesn't have PR functionality. This would need to
        use the appropriate CLI tool (gh, glab) based on the repository type.
        """
        try:
            # Attempt to detect underlying VCS and use appropriate tool
            git_url = os.getenv("GIT_URL", "")
            
            if "github.com" in git_url:
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
                    
            elif "gitlab" in git_url:
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
            print(f"Error creating PR from Jenkins: {e}")
            return None

    def get_environment_variables(self) -> Dict[str, str]:
        """Get Jenkins environment variables."""
        jenkins_vars = {}
        for key, value in os.environ.items():
            if (
                key.startswith("JENKINS_")
                or key.startswith("HUDSON_")
                or key.startswith("GIT_")
                or key.startswith("BUILD_")
                or key.startswith("JOB_")
            ):
                jenkins_vars[key] = value
        return jenkins_vars

    def _get_branch_name(self) -> str:
        """Get current branch name."""
        # Try different Jenkins variables
        branch = os.getenv("GIT_BRANCH") or os.getenv("BRANCH_NAME") or os.getenv("gitlabBranch")
        
        if branch:
            # Remove origin/ prefix if present
            if branch.startswith("origin/"):
                branch = branch.replace("origin/", "")
            return branch
        return "main"

    def _get_event_type(self) -> str:
        """Determine the event type that triggered the build."""
        # Jenkins doesn't have a standard event type, but we can infer
        if os.getenv("CHANGE_ID"):
            return "pull_request"
        elif os.getenv("TAG_NAME"):
            return "tag"
        return "push"

    def _configure_git(self):
        """Configure git for commits."""
        repo_path = self.get_repository_path()

        # Set git user from Jenkins environment or use defaults
        user_name = os.getenv("BUILD_USER", "jenkins")
        user_email = os.getenv("BUILD_USER_EMAIL", "jenkins@localhost")

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

