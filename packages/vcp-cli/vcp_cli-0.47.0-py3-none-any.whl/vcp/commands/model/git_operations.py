"""Consolidated Git operations for model workspace management."""

import json
import logging
import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from git import Repo

from ...auth.github import GitHubAuth
from ...config.config import Config

logger = logging.getLogger(__name__)


class GitOperations:
    """Consolidated Git operations for workspace management."""

    def __init__(self, repo_path: str, config: Config, debug: bool = False):
        """Initialize with repository path and config for GitHub authentication."""
        self.repo_path = Path(repo_path)
        self._repo: Optional[Repo] = None
        self.github_auth = GitHubAuth(config)
        self.debug = debug
        logger.debug(f"GitOperations initialized with repo_path={repo_path}")
        if self.debug:
            print(f"DEBUG: GitOperations initialized with repo_path={repo_path}")

    def _mask_token(self, token: str, show_chars: int = 4) -> str:
        """Mask sensitive token information for safe logging."""
        if not token or len(token) <= show_chars * 2:
            return "***"
        return f"{token[:show_chars]}...{token[-show_chars:]}"

    def _mask_sensitive_data(self, text: str) -> str:
        """Mask all sensitive information in text for safe sharing in tickets."""
        # Mask GitHub tokens (ghs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
        text = re.sub(r"ghs_[A-Za-z0-9]{36}", "ghs_***MASKED***", text)

        # Mask any token-like strings (40+ character alphanumeric)
        text = re.sub(r"\b[A-Za-z0-9]{40,}\b", "***TOKEN_MASKED***", text)

        # Mask URLs with embedded tokens
        text = re.sub(
            r"https://[^@]+@github\.com/", "https://***TOKEN***@github.com/", text
        )

        # Mask email addresses
        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "***EMAIL_MASKED***",
            text,
        )

        # Mask API keys and secrets (common patterns)
        text = re.sub(r"\b[A-Za-z0-9]{32,}\b", "***SECRET_MASKED***", text)

        return text

    def _is_github_url(self, url: str) -> bool:
        """Safely validate if a URL is a GitHub URL using proper URL parsing."""
        try:
            parsed = urlparse(url)
            # Check if the hostname is exactly github.com (not a subdomain or malicious domain)
            return parsed.hostname == "github.com" and parsed.scheme in (
                "https",
                "http",
            )
        except Exception:
            return False

    def _extract_github_repo_path(self, url: str) -> Optional[str]:
        """Extract the repository path from a GitHub URL safely."""
        try:
            parsed = urlparse(url)
            if parsed.hostname == "github.com" and parsed.path:
                # Remove leading slash and return the path
                return parsed.path.lstrip("/")
        except Exception:
            pass
        return None

    @property
    def repo(self) -> Optional[Repo]:
        """Get repository object with lazy loading."""
        if self._repo is None and (self.repo_path / ".git").exists():
            try:
                self._repo = Repo(self.repo_path)
            except Exception as e:
                logger.error(f"Failed to initialize git repository: {e}")
                return None
        return self._repo

    def _setup_git_authentication(self):
        """Set up Git authentication environment to prevent password prompts."""
        try:
            token = self.github_auth.get_contributions_token()
        except Exception:
            return None, None

        # Store original environment variables
        original_askpass = os.environ.get("GIT_ASKPASS")
        original_ssh_askpass = os.environ.get("SSH_ASKPASS")
        original_terminal_prompt = os.environ.get("GIT_TERMINAL_PROMPT")

        # Disable interactive prompts and set up credential helper
        os.environ["GIT_TERMINAL_PROMPT"] = "0"

        # Try to use credential helper to avoid password prompts
        # This tells git to use the embedded token in the URL
        os.environ["GIT_CONFIG_GLOBAL"] = (
            "/dev/null"  # Prevent global git config interference
        )

        # Create a temporary askpass script that returns the token
        askpass_path = None
        try:
            # Try to create temporary file in /tmp first, then fallback to current directory
            temp_dirs = ["/tmp", str(Path.cwd()), os.path.expanduser("~")]
            logger.debug(f"Trying to create askpass script in directories: {temp_dirs}")

            for temp_dir in temp_dirs:
                try:
                    logger.debug(f"Checking directory: {temp_dir}")
                    logger.debug(f"Directory exists: {os.path.exists(temp_dir)}")
                    logger.debug(
                        f"Directory writable: {os.access(temp_dir, os.W_OK) if os.path.exists(temp_dir) else 'N/A'}"
                    )

                    if os.path.exists(temp_dir) and os.access(temp_dir, os.W_OK):
                        with tempfile.NamedTemporaryFile(
                            mode="w", delete=False, suffix=".sh", dir=temp_dir
                        ) as askpass_file:
                            askpass_file.write(f"#!/bin/sh\necho '{token}'\n")
                            askpass_file.flush()
                            os.fsync(
                                askpass_file.fileno()
                            )  # Ensure data is written to disk
                            askpass_path = askpass_file.name
                            logger.debug(
                                f"Successfully created askpass script at: {askpass_path}"
                            )
                        break
                except (OSError, PermissionError) as e:
                    logger.debug(f"Failed to create askpass script in {temp_dir}: {e}")
                    continue

            if not askpass_path:
                logger.warning(
                    "Could not create temporary askpass script in any writable directory"
                )
                # Fallback to using the embedded token URL directly
                # Don't set GIT_ASKPASS, rely on the embedded token in the URL
            else:
                # Make the script executable
                os.chmod(askpass_path, stat.S_IRWXU)
                os.environ["GIT_ASKPASS"] = askpass_path
                os.environ["SSH_ASKPASS"] = askpass_path
                logger.debug(f"Created askpass script at: {askpass_path}")

        except Exception as e:
            logger.warning(f"Failed to create askpass script: {e}")
            # Fallback to using the embedded token URL directly
            # Don't set GIT_ASKPASS, rely on the embedded token in the URL

        return (
            original_askpass,
            original_ssh_askpass,
            original_terminal_prompt,
        ), askpass_path

    def _cleanup_git_authentication(self, original_env_vars, askpass_file_path):
        """Clean up Git authentication environment."""
        if not original_env_vars or not askpass_file_path:
            return

        # Restore original environment variables
        original_askpass, original_ssh_askpass, original_terminal_prompt = (
            original_env_vars
        )

        if original_askpass is not None:
            os.environ["GIT_ASKPASS"] = original_askpass
        else:
            os.environ.pop("GIT_ASKPASS", None)

        if original_ssh_askpass is not None:
            os.environ["SSH_ASKPASS"] = original_ssh_askpass
        else:
            os.environ.pop("SSH_ASKPASS", None)

        if original_terminal_prompt is not None:
            os.environ["GIT_TERMINAL_PROMPT"] = original_terminal_prompt
        else:
            os.environ.pop("GIT_TERMINAL_PROMPT", None)

        # Clean up temporary askpass file
        try:
            os.unlink(askpass_file_path)
        except OSError:
            pass  # File might already be deleted

    def _run_git_command_with_auth(
        self, command: list, timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """Run a git command with authentication setup."""
        try:
            self.github_auth.get_contributions_token()
        except Exception:
            # No token available, run command without authentication
            return subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        # Set up authentication environment
        original_env_vars, askpass_file_path = self._setup_git_authentication()

        try:
            # Log the command (without sensitive info)
            safe_command = " ".join(command)
            logger.debug(f"Running git command: {safe_command}")
            logger.debug(f"GIT_ASKPASS: {os.environ.get('GIT_ASKPASS', 'Not set')}")
            logger.debug(
                f"GIT_TERMINAL_PROMPT: {os.environ.get('GIT_TERMINAL_PROMPT', 'Not set')}"
            )
            logger.debug(
                f"GIT_CONFIG_GLOBAL: {os.environ.get('GIT_CONFIG_GLOBAL', 'Not set')}"
            )
            logger.debug(f"Working directory: {self.repo_path}")
            logger.debug(
                f"Git version: {subprocess.run(['git', '--version'], capture_output=True, text=True).stdout.strip()}"
            )

            # Log environment variables that might affect Git
            git_env_vars = {k: v for k, v in os.environ.items() if k.startswith("GIT_")}
            logger.debug(f"Git environment variables: {git_env_vars}")

            # Try multiple authentication approaches
            auth_methods = [
                # Method 1: With GIT_ASKPASS (if script was created)
                {"env": os.environ.copy(), "name": "with GIT_ASKPASS"},
                # Method 2: Without GIT_ASKPASS (rely on embedded token in URL)
                {
                    "env": {
                        k: v
                        for k, v in os.environ.items()
                        if k not in ["GIT_ASKPASS", "SSH_ASKPASS"]
                    },
                    "name": "without GIT_ASKPASS",
                },
            ]

            result = None
            for i, method in enumerate(auth_methods, 1):
                logger.debug(f"Trying authentication method {i}: {method['name']}")

                result = subprocess.run(
                    command,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=method["env"],
                )

                if result.returncode == 0:
                    logger.info(
                        f"Successfully executed git command using authentication method {i}"
                    )
                    break
                else:
                    error_msg = result.stderr.strip()
                    logger.debug(f"Authentication method {i} failed: {error_msg}")

                    # If this is a password prompt, try the next method
                    if (
                        "Password for" in error_msg
                        or "Authentication failed" in error_msg
                    ):
                        logger.warning(
                            f"Password prompt detected with method {i}, trying next method..."
                        )
                        continue
                    else:
                        # If it's not a password prompt, this might be a different error
                        logger.debug(
                            f"Non-authentication error with method {i}: {error_msg}"
                        )
                        break

            if result is None or result.returncode != 0:
                error_msg = (
                    result.stderr.strip()
                    if result
                    else "All authentication methods failed"
                )
                logger.error(f"All authentication methods failed: {error_msg}")

            return result
        finally:
            self._cleanup_git_authentication(original_env_vars, askpass_file_path)

    def is_git_repository(self) -> bool:
        """Check if path is a git repository."""
        return (self.repo_path / ".git").exists() and self.repo is not None

    def is_valid_workspace(self, metadata_file: str = ".model-metadata") -> bool:
        """Check if directory is a valid model workspace.

        Args:
            metadata_file: Name of the metadata file to check for

        Returns:
            True if directory exists, has metadata file, and is a git repository
        """
        metadata_path = self.repo_path / metadata_file
        return (
            self.repo_path.exists()
            and metadata_path.exists()
            and self.is_git_repository()
        )

    def get_basic_status(self) -> Dict:
        """Get basic git repository status."""
        if not self.is_git_repository():
            return {"status": "no_git"}

        try:
            repo = self.repo
            return {
                "status": "git_repo",
                "current_branch": repo.active_branch.name
                if repo.active_branch
                else None,
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files,
                "remote_url": repo.remotes.origin.url if repo.remotes else None,
                "has_commits": len(list(repo.iter_commits())) > 0,
            }
        except Exception as e:
            logger.error(f"Failed to get git status: {e}")
            return {"status": "git_error", "error": str(e)}

    def has_user_changes(self) -> bool:
        """Check if repository has user modifications beyond initial commit."""
        if not self.is_git_repository():
            return False

        try:
            repo = self.repo
            # Check if there are more than 1 commit (initial + user changes)
            commits = list(repo.iter_commits())
            return len(commits) > 1
        except Exception:
            return False

    def branch_exists(self, branch_name: str) -> Tuple[bool, str]:
        """Check if branch exists locally or remotely.

        Returns:
            Tuple of (exists, location) where location is 'local', 'remote', or 'both'
        """
        if not self.is_git_repository():
            return False, "no_git"

        try:
            repo = self.repo

            # Check local branches
            local_exists = branch_name in [branch.name for branch in repo.branches]

            # Check remote branches
            remote_exists = False
            try:
                repo.git.ls_remote("--heads", "origin", branch_name)
                remote_exists = True
            except Exception:
                pass

            if local_exists and remote_exists:
                return True, "both"
            elif local_exists:
                return True, "local"
            elif remote_exists:
                return True, "remote"
            else:
                return False, "none"

        except Exception as e:
            logger.error(f"Failed to check branch existence: {e}")
            return False, "error"

    def get_remote_branch_status(self, branch_name: str) -> Dict:
        """Get detailed status of remote branch."""
        if not self.is_git_repository():
            return {"error": "no_git"}

        try:
            repo = self.repo
            repo.remotes.origin.fetch()

            # Check if remote branch exists
            remote_branches = [ref.name for ref in repo.remotes.origin.refs]
            if branch_name not in remote_branches:
                return {"exists": False}

            # Check if local is behind/ahead of remote
            try:
                behind_count = len(
                    list(repo.iter_commits(f"HEAD..origin/{branch_name}"))
                )
                ahead_count = len(
                    list(repo.iter_commits(f"origin/{branch_name}..HEAD"))
                )

                return {
                    "exists": True,
                    "behind_count": behind_count,
                    "ahead_count": ahead_count,
                    "needs_pull": behind_count > 0,
                    "needs_push": ahead_count > 0,
                }
            except Exception:
                return {"exists": True, "error": "Could not compare commits"}

        except Exception as e:
            logger.error(f"Failed to get remote branch status: {e}")
            return {"error": str(e)}

    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout an existing branch."""
        if not self.is_git_repository():
            return False

        try:
            repo = self.repo

            # Check if branch exists locally
            if branch_name in [branch.name for branch in repo.branches]:
                repo.git.checkout(branch_name)
                logger.debug(f"Checked out existing local branch: {branch_name}")
                return True

            # Check if branch exists remotely
            try:
                repo.git.checkout("-b", branch_name, f"origin/{branch_name}")
                logger.debug(f"Checked out remote branch: {branch_name}")
                return True
            except Exception:
                logger.warning(
                    f"Branch {branch_name} does not exist locally or remotely"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to checkout branch {branch_name}: {e}")
            return False

    def create_branch(self, branch_name: str) -> bool:
        """Create a new branch from main."""
        if not self.is_git_repository():
            return False

        try:
            repo = self.repo
            logger.debug(
                f"Creating branch {branch_name} in repository at {self.repo_path}"
            )

            # Ensure we're on main branch
            if repo.active_branch.name != "main":
                logger.debug(f"Checking out main branch from {repo.active_branch.name}")
                repo.git.checkout("main")

            # Pull latest changes from main using authenticated approach
            try:
                token = self.github_auth.get_contributions_token()
                remote_url = repo.remotes.origin.url
                if self.debug:
                    print(f"DEBUG: Remote URL: {self._mask_sensitive_data(remote_url)}")
                    print(f"DEBUG: Using token: {self._mask_token(token)}")
                    print(f"DEBUG: Token length: {len(token)}")
                else:
                    logger.debug(f"Remote URL: {self._mask_sensitive_data(remote_url)}")
                    logger.debug(f"Using token: {self._mask_token(token)}")
                    logger.debug(f"Token length: {len(token)}")

                # Check if it's a GitHub URL using proper URL parsing
                if self._is_github_url(remote_url):
                    # Extract the repository path safely
                    repo_path = self._extract_github_repo_path(remote_url)
                    if repo_path:
                        # Always use the fresh token we just retrieved
                        auth_url = f"https://{token}@github.com/{repo_path}"
                        if self.debug:
                            print(
                                f"DEBUG: Created authenticated GitHub URL: {self._mask_sensitive_data(auth_url)}"
                            )
                        else:
                            logger.debug("Created authenticated GitHub URL")
                    else:
                        logger.warning(
                            "Could not extract repository path from GitHub URL"
                        )
                        auth_url = remote_url

                    # Use the robust _run_git_command_with_auth method instead of direct subprocess
                    if self.debug:
                        print("DEBUG: Using _run_git_command_with_auth for git pull")
                    result = self._run_git_command_with_auth([
                        "git",
                        "pull",
                        auth_url,
                        "main",
                    ])
                    if self.debug:
                        print(f"DEBUG: Git pull result: returncode={result.returncode}")
                        print(f"DEBUG: Git pull stdout: {result.stdout}")
                        print(f"DEBUG: Git pull stderr: {result.stderr}")
                    else:
                        logger.debug(f"Git pull result: returncode={result.returncode}")
                        logger.debug(f"Git pull stdout: {result.stdout}")
                        logger.debug(f"Git pull stderr: {result.stderr}")

                    if result.returncode != 0:
                        print(f"ERROR: Failed to pull main branch: {result.stderr}")
                        return False
                else:
                    # Fallback to GitPython if not a GitHub URL
                    if self.debug:
                        print("DEBUG: Using GitPython fallback for non-GitHub URL")
                    else:
                        logger.debug("Using GitPython fallback for non-GitHub URL")
                    repo.git.pull("origin", "main")
            except Exception as e:
                # Token retrieval failed, use GitPython (may prompt for password)
                print(
                    f"WARNING: Failed to get GitHub token: {e}, using GitPython (may prompt for password)"
                )
                repo.git.pull("origin", "main")

            # Create and checkout new branch
            logger.debug(f"Creating new branch: {branch_name}")
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()

            logger.debug(f"Created and checked out branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False

    def update_main_branch(self) -> bool:
        """Update main branch with latest changes from remote."""
        if not self.is_git_repository():
            return False

        try:
            repo = self.repo

            # Checkout main branch
            if repo.active_branch.name != "main":
                repo.git.checkout("main")

            # Pull latest changes using authenticated command
            try:
                token = self.github_auth.get_contributions_token()
                # Get the remote URL and convert it to authenticated URL
                remote_url = repo.remotes.origin.url
                if remote_url.startswith("https://github.com/"):
                    auth_url = remote_url.replace(
                        "https://github.com/",
                        f"https://{token}@github.com/",
                    )
                    # Use embedded token URL approach for git pull
                    result = self._run_git_command_with_auth([
                        "git",
                        "pull",
                        auth_url,
                        "main",
                    ])
                else:
                    # Fallback to regular git pull with authentication
                    result = self._run_git_command_with_auth([
                        "git",
                        "pull",
                        "origin",
                        "main",
                    ])

                if result.returncode != 0:
                    logger.error(f"Failed to pull main branch: {result.stderr}")
                    return False
            except Exception as e:
                # Token retrieval failed, use GitPython (may prompt for password)
                logger.warning(
                    f"Failed to get GitHub token: {e}, using GitPython (may prompt for password)"
                )
                repo.git.pull("origin", "main")

            logger.debug("Updated main branch with latest changes")
            return True
        except Exception as e:
            logger.error(f"Failed to update main branch: {e}")
            return False

    def update_model_branch(self, branch_name: str) -> bool:
        """Update the model branch with latest changes from main."""
        if not self.is_git_repository():
            return False

        try:
            repo = self.repo

            # Ensure we're on the model branch
            if repo.active_branch.name != branch_name:
                repo.git.checkout(branch_name)

            # Merge latest changes from main into the model branch using authenticated command
            try:
                self.github_auth.get_contributions_token()
                result = self._run_git_command_with_auth([
                    "git",
                    "merge",
                    "origin/main",
                ])
                if result.returncode != 0:
                    logger.error(
                        f"Failed to merge main into {branch_name}: {result.stderr}"
                    )
                    return False
            except Exception as e:
                # Token retrieval failed, use GitPython (may prompt for password)
                logger.warning(
                    f"Failed to get GitHub token: {e}, using GitPython (may prompt for password)"
                )
                repo.git.merge("origin/main")

            logger.debug(
                f"Updated model branch {branch_name} with latest changes from main"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update model branch {branch_name}: {e}")
            return False

    def get_workspace_info(self) -> Dict:
        """Get comprehensive workspace information.

        Returns:
            Dictionary with workspace status, git info, and metadata info
        """
        info = {
            "workspace_path": str(self.repo_path),
            "is_valid_workspace": self.is_valid_workspace(),
            "is_git_repository": self.is_git_repository(),
            "git_status": self.get_basic_status(),
        }

        # Add metadata file info if it exists
        metadata_file = self.repo_path / ".model-metadata"
        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)
                info["metadata"] = metadata
            except Exception as e:
                logger.warning(f"Failed to read metadata file: {e}")
                info["metadata_error"] = str(e)

        return info

    def get_branch_info(self, branch_name: str) -> Dict:
        """Get comprehensive information about a specific branch.

        Args:
            branch_name: Name of the branch to analyze

        Returns:
            Dictionary with branch existence, location, and status
        """
        exists, location = self.branch_exists(branch_name)
        remote_status = self.get_remote_branch_status(branch_name)

        return {
            "branch_name": branch_name,
            "exists": exists,
            "location": location,
            "remote_status": remote_status,
            "is_current": self.get_basic_status().get("current_branch") == branch_name,
        }
