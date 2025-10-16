"""GitHub authentication utilities for CLI."""

import logging
import os
import shutil
import stat
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from git import Git, Repo

from ..config.config import Config

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Immutable token information with expiration tracking."""

    token: str
    expires_at: float
    created_at: float

    @property
    def is_expired(self) -> bool:
        """Check if token is expired with 5-minute safety buffer."""
        return time.time() >= (self.expires_at - 300)  # 5-minute buffer

    @property
    def ttl_seconds(self) -> int:
        """Get time-to-live in seconds."""
        return max(0, int(self.expires_at - time.time()))

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not None)."""
        return bool(self.token and not self.is_expired)


class GitHubAuth:
    """Handles GitHub authentication for CLI operations with thread safety."""

    def __init__(self, config: Config):
        """Initialize GitHub authentication."""
        self.config = config
        self._token_info: Optional[TokenInfo] = None
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._api_failure_count = 0
        self._max_api_failures = 3
        self._last_api_failure_time: Optional[float] = None

    def get_contributions_token(self) -> str:
        """Get GitHub contributions access token from Model Hub API with thread safety."""
        with self._lock:
            # Fast path: return valid cached token
            if self._token_info and self._token_info.is_valid:
                return self._token_info.token

            # Clear expired token
            if self._token_info and self._token_info.is_expired:
                logger.debug("GitHub token has expired, generating new token")
                self._token_info = None

            # Generate new token (includes circuit breaker logic)
            return self._generate_new_token()

    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open due to repeated API failures."""
        if self._api_failure_count < self._max_api_failures:
            return False

        # Reset circuit breaker after 5 minutes
        if (
            self._last_api_failure_time
            and time.time() - self._last_api_failure_time > 300
        ):
            logger.debug("Resetting GitHub token API circuit breaker")
            self._api_failure_count = 0
            self._last_api_failure_time = None
            return False

        return True

    def _generate_new_token(self) -> str:
        """Generate a new token with retry logic and error handling."""
        # Check circuit breaker before attempting
        if self._is_circuit_breaker_open():
            raise RuntimeError(
                "GitHub token API is temporarily unavailable due to repeated failures. "
                "Please try again later or run 'vcp login' to refresh authentication."
            )

        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                # Import TokenManager here to avoid circular imports
                from ..utils.token import TokenManager  # noqa: PLC0415

                # Get authentication headers for the Model Hub API
                token_manager = TokenManager()
                headers = token_manager.get_auth_headers()

                if not headers:
                    raise RuntimeError(
                        "Not logged in to Model Hub. Please run 'vcp login' first to authenticate."
                    )

                # Get contributions token from Model Hub API
                token_url = (
                    f"{self.config.models.base_url}/api/github/contribution/app/token"
                )

                # Add timeout configuration
                response = requests.get(token_url, headers=headers, timeout=30)
                response.raise_for_status()

                token_data = response.json()
                if "token" not in token_data:
                    raise KeyError("Missing 'token' field in API response")

                token = token_data["token"]
                if not token or not isinstance(token, str):
                    raise ValueError("Invalid token received from API")

                # Create immutable token info
                current_time = time.time()
                self._token_info = TokenInfo(
                    token=token,
                    expires_at=current_time + (55 * 60),  # 55 minutes
                    created_at=current_time,
                )

                # Reset failure count on success
                self._api_failure_count = 0
                self._last_api_failure_time = None

                logger.debug(
                    f"Successfully retrieved GitHub contributions token from Model Hub "
                    f"(TTL: {self._token_info.ttl_seconds}s)"
                )
                return token

            except (requests.exceptions.RequestException, KeyError, ValueError) as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Failed to get GitHub token (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Only increment failure count after all retries are exhausted
                    self._api_failure_count += 1
                    self._last_api_failure_time = time.time()

                    logger.error(
                        f"Failed to get GitHub contributions token after {max_retries} attempts: {e}"
                    )
                    if isinstance(e, requests.exceptions.RequestException):
                        raise RuntimeError(
                            "Failed to authenticate with GitHub contributions. Please ensure you are logged in to the Model Hub "
                            "and have completed GitHub OAuth authentication for the contributions organization."
                        ) from e
                    elif isinstance(e, KeyError):
                        raise RuntimeError("Invalid response from Model Hub API") from e
                    else:
                        raise RuntimeError(
                            f"Invalid token received from Model Hub API: {e}"
                        ) from e

    def force_token_refresh(self) -> str:
        """Force refresh of the GitHub contributions token."""
        with self._lock:
            logger.debug("Forcing GitHub token refresh")
            self._token_info = None
            # Reset circuit breaker to allow immediate retry
            self._api_failure_count = 0
            self._last_api_failure_time = None
            return self.get_contributions_token()

    def is_token_expired(self) -> bool:
        """Check if the current token is expired."""
        with self._lock:
            return not self._token_info or self._token_info.is_expired

    def get_token_ttl_seconds(self) -> Optional[int]:
        """Get the time-to-live (TTL) of the current token in seconds."""
        with self._lock:
            return self._token_info.ttl_seconds if self._token_info else None

    def get_token_info(self) -> Optional[TokenInfo]:
        """Get current token information (for debugging/monitoring)."""
        with self._lock:
            return self._token_info

    def validate_token_with_github(self) -> bool:
        """Validate the current token by making a test API call to GitHub."""
        with self._lock:
            if not self._token_info or not self._token_info.is_valid:
                return False

            try:
                headers = {"Authorization": f"token {self._token_info.token}"}
                response = requests.get(
                    "https://api.github.com/user", headers=headers, timeout=10
                )
                return response.status_code == 200
            except Exception as e:
                logger.warning(f"Token validation failed: {e}")
                return False

    def clone_repository(self, repo_url: str, output_path: str) -> Repo:
        """Clone a repository using GitHub App installation token with robust authentication."""

        try:
            token = self.get_contributions_token()

            # For GitHub App installation tokens, we need to use the token directly
            # GitHub App tokens don't need x-access-token prefix
            if repo_url.startswith("https://github.com/"):
                # Convert to authenticated URL with GitHub App token
                auth_url = repo_url.replace(
                    "https://github.com/", f"https://{token}@github.com/"
                )
            else:
                auth_url = repo_url

            # Set up authentication environment
            original_terminal_prompt = os.environ.get("GIT_TERMINAL_PROMPT")
            original_askpass = os.environ.get("GIT_ASKPASS")

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

                for temp_dir in temp_dirs:
                    try:
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
                            break
                    except (OSError, PermissionError):
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
                    logger.debug(f"Created askpass script at: {askpass_path}")

            except Exception as e:
                logger.warning(f"Failed to create askpass script: {e}")
                # Fallback to using the embedded token URL directly
                # Don't set GIT_ASKPASS, rely on the embedded token in the URL

            try:
                # Log the authentication URL (without the token for security)
                safe_url = auth_url.replace(token, "***TOKEN***")
                logger.debug(f"Cloning repository with URL: {safe_url}")
                logger.debug(f"GIT_ASKPASS: {os.environ.get('GIT_ASKPASS', 'Not set')}")
                logger.debug(
                    f"GIT_TERMINAL_PROMPT: {os.environ.get('GIT_TERMINAL_PROMPT', 'Not set')}"
                )

                # Try multiple authentication approaches
                auth_methods = [
                    # Method 1: Embedded token URL with GIT_ASKPASS
                    {"url": auth_url, "env": os.environ.copy()},
                    # Method 2: Embedded token URL without GIT_ASKPASS
                    {
                        "url": auth_url,
                        "env": {
                            k: v for k, v in os.environ.items() if k != "GIT_ASKPASS"
                        },
                    },
                    # Method 3: Original URL with GIT_ASKPASS only
                    {"url": repo_url, "env": os.environ.copy()},
                ]

                result = None
                for i, method in enumerate(auth_methods, 1):
                    logger.debug(
                        f"Trying authentication method {i}: {'with' if 'GIT_ASKPASS' in method['env'] else 'without'} GIT_ASKPASS"
                    )

                    result = subprocess.run(
                        ["git", "clone", method["url"], output_path],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        env=method["env"],
                    )

                    if result.returncode == 0:
                        logger.info(
                            f"Successfully cloned repository using authentication method {i}"
                        )
                        break
                    else:
                        logger.debug(
                            f"Authentication method {i} failed: {result.stderr.strip()}"
                        )
                        # Clean up partial clone if it exists
                        if os.path.exists(output_path):
                            shutil.rmtree(output_path, ignore_errors=True)

                if result is None or result.returncode != 0:
                    error_msg = (
                        result.stderr.strip()
                        if result
                        else "All authentication methods failed"
                    )
                    logger.error(
                        f"Git clone failed after trying all authentication methods: {error_msg}"
                    )
                    if result:
                        logger.debug(f"Git clone stdout: {result.stdout}")

                    # Provide more helpful error message for SAML SSO issues
                    if "SAML SSO" in error_msg or "403" in error_msg:
                        raise RuntimeError(
                            f"Failed to clone repository due to SAML SSO authentication. "
                            f"The GitHub App installation token may need to be authorized for the organization. "
                            f"Please ensure the GitHub App is properly installed and authorized for the 'cz-model-contributions' organization. "
                            f"Original error: {error_msg}"
                        )
                    elif (
                        "Authentication failed" in error_msg
                        or "Invalid username or token" in error_msg
                        or "Password for" in error_msg
                    ):
                        raise RuntimeError(
                            f"Failed to clone repository due to authentication issues. "
                            f"The GitHub token may be expired or invalid. "
                            f"Please run 'vcp login' to refresh your authentication. "
                            f"Original error: {error_msg}"
                        )
                    else:
                        raise RuntimeError(f"Failed to clone repository: {error_msg}")

                # Create Repo object from the cloned directory
                repo = Repo(output_path)
                logger.debug(f"Successfully cloned repository to {output_path}")
                return repo

            finally:
                # Clean up authentication environment
                if original_terminal_prompt is not None:
                    os.environ["GIT_TERMINAL_PROMPT"] = original_terminal_prompt
                else:
                    os.environ.pop("GIT_TERMINAL_PROMPT", None)

                if original_askpass is not None:
                    os.environ["GIT_ASKPASS"] = original_askpass
                else:
                    os.environ.pop("GIT_ASKPASS", None)

                # Remove temporary askpass file
                if askpass_path:
                    try:
                        os.unlink(askpass_path)
                    except OSError:
                        pass  # File might already be deleted

        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise RuntimeError(f"Failed to clone repository: {e}") from e

    def clone_repository_branch(
        self, repo_url: str, output_path: str, branch_name: str
    ) -> Repo:
        """Clone a specific branch of a repository using GitHub App installation token."""

        try:
            token = self.get_contributions_token()

            # For GitHub App installation tokens, we need to use the token directly
            # GitHub App tokens don't need x-access-token prefix
            if repo_url.startswith("https://github.com/"):
                # Convert to authenticated URL with GitHub App token
                auth_url = repo_url.replace(
                    "https://github.com/", f"https://{token}@github.com/"
                )
            else:
                auth_url = repo_url

            # Create a temporary askpass script that returns the token
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".sh"
            ) as askpass_file:
                askpass_file.write(f"#!/bin/sh\necho '{token}'\n")
                askpass_file.flush()

                # Make the script executable
                os.chmod(askpass_file.name, stat.S_IRWXU)

                # Set up environment for Git
                original_askpass = os.environ.get("GIT_ASKPASS")
                os.environ["GIT_ASKPASS"] = askpass_file.name

                try:
                    # Clone with specific branch
                    git = Git()
                    git.clone(auth_url, output_path, branch=branch_name)

                    # Create Repo object from the cloned directory
                    repo = Repo(output_path)

                    return repo

                finally:
                    # Clean up
                    if original_askpass is not None:
                        os.environ["GIT_ASKPASS"] = original_askpass
                    else:
                        os.environ.pop("GIT_ASKPASS", None)

                    # Remove temporary file
                    try:
                        os.unlink(askpass_file.name)
                    except OSError:
                        pass  # File might already be deleted

        except Exception as e:
            logger.error(f"Failed to clone repository branch '{branch_name}': {e}")
            # Provide more helpful error message for SAML SSO issues
            if "SAML SSO" in str(e) or "403" in str(e):
                raise RuntimeError(
                    f"Failed to clone repository branch due to SAML SSO authentication. "
                    f"The GitHub App installation token may need to be authorized for the organization. "
                    f"Please ensure the GitHub App is properly installed and authorized for the 'cz-model-contributions' organization. "
                    f"Original error: {e}"
                ) from e
            else:
                raise RuntimeError(
                    f"Failed to clone repository branch '{branch_name}': {e}"
                ) from e

    def test_contributions_authentication(self) -> bool:
        """Test if GitHub contributions authentication is working."""
        try:
            token = self.get_contributions_token()
            # Test the token by making a simple GitHub API call
            headers = {"Authorization": f"token {token}"}
            response = requests.get("https://api.github.com/user", headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"GitHub contributions authentication test failed: {e}")
            return False

    def create_branch(self, repo_path: str, branch_name: str) -> bool:
        """Create a new branch from main."""
        try:
            repo = Repo(repo_path)
            logger.debug(f"Creating branch {branch_name} in repository at {repo_path}")

            # Ensure we're on main branch
            if repo.active_branch.name != "main":
                logger.debug(f"Checking out main branch from {repo.active_branch.name}")
                repo.git.checkout("main")

            # Pull latest changes from main using authenticated approach
            token = self.get_contributions_token()
            remote_url = repo.remotes.origin.url
            logger.debug(f"Remote URL: {remote_url}")
            logger.debug(f"Using token: {token[:10]}..." if token else "No token")

            if remote_url.startswith("https://github.com/"):
                auth_url = remote_url.replace(
                    "https://github.com/", f"https://{token}@github.com/"
                )
                logger.debug(
                    f"Using authenticated URL: {auth_url.replace(token, '***TOKEN***')}"
                )

                # Use subprocess with embedded token URL for git pull
                result = subprocess.run(
                    ["git", "pull", auth_url, "main"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                logger.debug(f"Git pull result: returncode={result.returncode}")
                logger.debug(f"Git pull stdout: {result.stdout}")
                logger.debug(f"Git pull stderr: {result.stderr}")

                if result.returncode != 0:
                    logger.error(f"Failed to pull main branch: {result.stderr}")
                    return False
            else:
                # Fallback to GitPython if not a GitHub URL
                logger.debug("Using GitPython fallback for non-GitHub URL")
                repo.git.pull("origin", "main")

            # Create and checkout new branch
            logger.debug(f"Creating new branch: {branch_name}")
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()

            logger.info(f"Created and checked out branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False

    def checkout_branch(self, repo_path: str, branch_name: str) -> bool:
        """Checkout an existing branch."""
        try:
            repo = Repo(repo_path)

            # Check if branch exists locally
            if branch_name in [branch.name for branch in repo.branches]:
                repo.git.checkout(branch_name)
                logger.info(f"Checked out existing local branch: {branch_name}")
                return True

            # Check if branch exists remotely
            try:
                repo.git.checkout("-b", branch_name, f"origin/{branch_name}")
                logger.info(f"Checked out remote branch: {branch_name}")
                return True
            except Exception:
                logger.warning(
                    f"Branch {branch_name} does not exist locally or remotely"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to checkout branch {branch_name}: {e}")
            return False

    def update_main_branch(self, repo_path: str) -> bool:
        """Update main branch with latest changes from remote."""
        try:
            repo = Repo(repo_path)

            # Checkout main branch
            if repo.active_branch.name != "main":
                repo.git.checkout("main")

            # Pull latest changes
            repo.git.pull("origin", "main")

            logger.info("Updated main branch with latest changes")
            return True
        except Exception as e:
            logger.error(f"Failed to update main branch: {e}")
            return False

    def check_branch_exists(self, repo_path: str, branch_name: str) -> bool:
        """Check if a branch exists locally or remotely."""
        try:
            repo = Repo(repo_path)

            # Check local branches
            if branch_name in [branch.name for branch in repo.branches]:
                return True

            # Check remote branches
            try:
                repo.git.ls_remote("--heads", "origin", branch_name)
                return True
            except Exception:
                return False

        except Exception as e:
            logger.error(f"Failed to check if branch {branch_name} exists: {e}")
            return False

    def check_pr_exists(
        self, repo_owner: str, repo_name: str, branch_name: str
    ) -> bool:
        """Check if a pull request exists for the given branch."""
        try:
            token = self.get_contributions_token()
            headers = {"Authorization": f"token {token}"}

            # GitHub API endpoint to list pull requests
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
            params = {"head": f"{repo_owner}:{branch_name}", "state": "open"}

            logger.debug(
                f"Checking PR for repo: {repo_owner}/{repo_name}, branch: {branch_name}"
            )
            logger.debug(f"API URL: {url}")
            logger.debug(f"API params: {params}")

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            prs = response.json()
            logger.debug(f"Found {len(prs)} PRs for branch {branch_name}")
            return len(prs) > 0

        except Exception as e:
            logger.error(f"Failed to check for PR for branch {branch_name}: {e}")
            logger.error(f"Repo: {repo_owner}/{repo_name}")
            return False

    def get_active_pr_details(
        self, repo_owner: str, repo_name: str, branch_name: str
    ) -> Optional[dict]:
        """Get details of the active PR for the given branch."""
        try:
            token = self.get_contributions_token()
            headers = {"Authorization": f"token {token}"}

            # GitHub API endpoint to list pull requests
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
            params = {"head": f"{repo_owner}:{branch_name}", "state": "open"}

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            prs = response.json()
            if len(prs) > 0:
                pr = prs[0]  # Get the first (and should be only) open PR
                return {
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "head_branch": pr.get("head", {}).get("ref"),
                    "base_branch": pr.get("base", {}).get("ref"),
                    "state": pr.get("state"),
                    "url": pr.get("html_url"),
                    "created_at": pr.get("created_at"),
                    "updated_at": pr.get("updated_at"),
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get PR details for branch {branch_name}: {e}")
            return None

    def get_repo_info(self, repo_url: str) -> tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        logger.debug(f"Parsing repository URL: {repo_url}")

        # Handle various GitHub URL formats
        if "github.com" in repo_url:
            # Remove protocol and domain, then split by /
            if repo_url.startswith("https://github.com/"):
                # https://github.com/owner/repo format
                path = repo_url.replace("https://github.com/", "").rstrip(".git")
            elif repo_url.startswith("git@github.com:"):
                # git@github.com:owner/repo format
                path = repo_url.replace("git@github.com:", "").rstrip(".git")
            else:
                # Handle other formats that might contain github.com
                # Extract the path after github.com/
                parts = repo_url.split("github.com/")
                if len(parts) > 1:
                    path = parts[1].rstrip(".git")
                else:
                    raise ValueError(
                        f"Could not extract path from GitHub URL: {repo_url}"
                    )

            # Split the path and extract owner/repo
            path_parts = path.split("/")
            logger.debug(f"URL path parts after parsing: {path_parts}")

            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                logger.debug(f"Extracted owner: {owner}, repo: {repo}")
                return owner, repo

        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    def update_model_branch(self, repo_path: str, branch_name: str) -> bool:
        """Update the model branch with latest changes from main."""
        try:
            repo = Repo(repo_path)

            # Ensure we're on the model branch
            if repo.active_branch.name != branch_name:
                repo.git.checkout(branch_name)

            # Merge latest changes from main into the model branch
            repo.git.merge("origin/main")

            logger.info(
                f"Updated model branch {branch_name} with latest changes from main"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update model branch {branch_name}: {e}")
            return False
