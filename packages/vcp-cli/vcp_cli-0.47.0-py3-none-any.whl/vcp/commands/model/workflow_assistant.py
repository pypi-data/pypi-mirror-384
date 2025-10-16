"""
VCP CLI Model Workflow Assistant

This module provides workflow assistance and guidance for the VCP CLI model commands.
It helps users understand the complete workflow and provides step-by-step guidance.
"""

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Tuple

import yaml
from rich.console import Console
from rich.table import Table

from .git_operations import GitOperations
from .utils import validate_init_command_ran, validate_stage_command_ran

logger = logging.getLogger(__name__)
console = Console()


class ModelWorkflowAssistant:
    """Assistant for guiding users through the VCP model workflow."""

    def __init__(self, config=None):
        """Initialize the workflow assistant."""
        # Cache for validation results to avoid duplicate error messages
        self._validation_cache = {}
        self.config = config
        self.workflow_steps = {
            1: {
                "command": "init",
                "name": "Initialize Model",
                "description": "Setup a new workdir for model packaging",
                "next_step": "metadata",
                "validation": self._validate_init_step,
            },
            2: {
                "command": "metadata",
                "name": "Review Files",
                "description": "Edit and validate metadata files",
                "next_step": "weights",
                "validation": self._validate_metadata_step,
            },
            3: {
                "command": "weights",
                "name": "Copy Weights",
                "description": "Copy model weights under model_data directory",
                "next_step": "package",
                "validation": self._validate_copy_weights_step,
            },
            4: {
                "command": "package",
                "name": "Package Model",
                "description": "Package the model",
                "next_step": "stage",
                "validation": self._validate_package_step,
            },
            5: {
                "command": "stage",
                "name": "Stage Files",
                "description": "Stage model artifacts",
                "next_step": "submit",
                "validation": self._validate_stage_step,
            },
            6: {
                "command": "submit",
                "name": "Submit Model",
                "description": "Submit model for review",
                "next_step": None,
                "validation": self._validate_submit_step,
            },
        }

        # Resubmission workflow (simplified)
        self.resubmission_workflow_steps = {
            1: {
                "command": "edit",
                "name": "Review and Edit Files",
                "description": "Review and edit model files",
                "next_step": "stage",
                "validation": self._validate_metadata_step,
            },
            2: {
                "command": "stage",
                "name": "Stage Files",
                "description": "Stage model artifacts",
                "next_step": "submit",
                "validation": self._validate_stage_step,
            },
            3: {
                "command": "submit",
                "name": "Submit Resubmission",
                "description": "Submit model resubmission",
                "next_step": None,
                "validation": self._validate_submit_step,
            },
        }

    def _clear_validation_cache(self):
        """Clear the validation cache."""
        self._validation_cache.clear()

    def _get_cached_validation(self, work_dir: str) -> Tuple[bool, str, dict]:
        """Get cached validation result or validate and cache it."""
        cache_key = f"init_validation_{work_dir}"
        if cache_key not in self._validation_cache:
            # Only show error messages on the first validation call
            is_valid, metadata_path, metadata = validate_init_command_ran(
                work_dir, verbose=True
            )
            self._validation_cache[cache_key] = (is_valid, metadata_path, metadata)
        else:
            # Use cached result without showing error messages
            is_valid, metadata_path, metadata = validate_init_command_ran(
                work_dir, verbose=False
            )
            # Update cache with fresh data but don't show errors
            self._validation_cache[cache_key] = (is_valid, metadata_path, metadata)
        return self._validation_cache[cache_key]

    def get_workflow_type(self, work_dir: str) -> str:
        """Determine if this is a resubmission or initial submission workflow."""
        try:
            is_valid, _metadata_path, metadata = self._get_cached_validation(work_dir)
            if is_valid and metadata.get("resubmit", False):
                return "resubmission"
            return "initial"
        except Exception:
            return "initial"

    def get_workflow_steps(self, work_dir: str) -> Dict:
        """Get the appropriate workflow steps based on the workflow type."""
        workflow_type = self.get_workflow_type(work_dir)
        if workflow_type == "resubmission":
            return self.resubmission_workflow_steps
        return self.workflow_steps

    def _validate_init_step(self, work_dir: str) -> Tuple[bool, str, Dict]:
        """Validate that init step was completed successfully."""
        try:
            # Use cached validation to avoid duplicate error messages
            is_valid, _metadata_path, metadata = self._get_cached_validation(work_dir)

            if not is_valid:
                return (
                    False,
                    "Run 'vcp model init' first to initialize a model packaging work-dir.",
                    {},
                )

            # Additional validation for required fields
            required_fields = [
                "model_name",
                "model_version",
                "license_type",
                "output_path",
            ]
            missing_fields = [
                field for field in required_fields if field not in metadata
            ]

            if missing_fields:
                return (
                    False,
                    f"Missing required fields in metadata: {missing_fields}",
                    metadata,
                )

            # Check for template files
            work_path = Path(work_dir)
            template_files = [
                "model_card_docs/model_card_metadata.yaml",
                "copier.yml",
                ".copier-answers.yml",
            ]

            missing_templates = []
            for template in template_files:
                if not (work_path / template).exists():
                    missing_templates.append(template)

            if missing_templates:
                return False, f"Missing template files: {missing_templates}", metadata

            return True, "Init step completed successfully", metadata

        except Exception as e:
            return False, f"Error validating init step: {e}", {}

    def _validate_stage_step(self, work_dir: str) -> Tuple[bool, str, Dict]:
        """Validate that stage step was completed successfully."""
        try:
            # Check if this is a resubmission workflow
            is_valid, _metadata_path, metadata = self._get_cached_validation(work_dir)
            if is_valid and metadata.get("resubmit", False):
                # Use resubmission-specific validation
                return self._validate_resubmit_stage_step(work_dir)

            # Original validation logic for initial submissions
            work_path = Path(work_dir)

            # Find mlflow package directory
            # TODO: remove wildcard from mlflow_pkg. Unnecessary and only used for backwards compatibility with testing repos
            mlflow_dirs = list(work_path.glob("*mlflow_pkg"))
            if not mlflow_dirs:
                return (
                    False,
                    "No *mlflow_pkg directory found. Run 'vcp model init' first.",
                    {},
                )

            mlflow_dir = mlflow_dirs[0]
            model_data_path = mlflow_dir / "model_data"

            if not model_data_path.exists():
                return (
                    False,
                    "No model_data directory found. Run 'vcp model init' first.",
                    {},
                )

            # Get all files for analysis
            all_files = list(model_data_path.rglob("*"))

            # First check if files are properly staged (only .ptr files remain)
            is_staged = validate_stage_command_ran(str(model_data_path))

            if is_staged:
                # Files are properly staged - count staged files
                ptr_files = [
                    f for f in all_files if f.is_file() and f.name.endswith(".ptr")
                ]
                return (
                    True,
                    f"Stage step completed successfully. {len(ptr_files)} files staged.",
                    {"staged_files": len(ptr_files)},
                )

            # If not staged, check if files have been added to git (which happens after staging)
            try:
                # Check git status to see if files are staged in git
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=work_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    # Check if there are any staged files (A = added, M = modified)
                    staged_files = [
                        line
                        for line in result.stdout.strip().split("\n")
                        if line and line[0] in "AM"
                    ]

                    if staged_files:
                        # Files have been added to git, which means staging was successful
                        return (
                            True,
                            f"Stage step completed successfully. {len(staged_files)} files added to git.",
                            {"staged_files": len(staged_files)},
                        )
            except Exception:
                # If git check fails, fall back to original validation
                pass

            # If neither staging nor git add worked, show error
            non_ptr_files = [
                f for f in all_files if f.is_file() and not f.name.endswith(".ptr")
            ]
            return (
                False,
                f"Found {len(non_ptr_files)} unstaged files. Run 'vcp model stage' to stage them.",
                {
                    "unstaged_files": [
                        str(f.relative_to(model_data_path)) for f in non_ptr_files[:10]
                    ]
                },
            )

        except Exception as e:
            return False, f"Error validating stage step: {e}", {}

    def _validate_resubmit_stage_step(self, work_dir: str) -> Tuple[bool, str, Dict]:
        """Validate that resubmission stage step was completed successfully."""
        try:
            # For resubmission, check if staging was successful by looking for .ptr files
            work_path = Path(work_dir)

            # Find mlflow package directory
            # TODO: remove wildcard from mlflow_pkg. Unnecessary and only used for backwards compatibility with testing repos
            mlflow_dirs = list(work_path.glob("*mlflow_pkg"))
            if not mlflow_dirs:
                return (
                    False,
                    "No *mlflow_pkg directory found. Run 'vcp model init' first.",
                    {},
                )

            mlflow_dir = mlflow_dirs[0]
            model_data_path = mlflow_dir / "model_data"

            if not model_data_path.exists():
                return (
                    False,
                    "No model_data directory found. Run 'vcp model init' first.",
                    {},
                )

            # For resubmission, check git status to see if files are staged
            try:
                # Check git status to see if files are staged in git
                result = subprocess.run(
                    ["git", "status"],
                    cwd=work_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    git_output = result.stdout

                    # Check if there are unstaged changes (should fail)
                    if (
                        '(use "git add <file>..." to update what will be committed)'
                        in git_output
                    ):
                        return (
                            False,
                            "Found unstaged changes. Run 'vcp model stage' to stage them for resubmission.",
                            {},
                        )

                    # Check if there are staged changes (should pass)
                    if "Changes to be committed:" in git_output:
                        return (
                            True,
                            "Staging completed successfully. Files are staged for resubmission.",
                            {"staged": True},
                        )

                    # If no changes at all, check for .ptr files as fallback
                    ptr_files = list(model_data_path.rglob("*.ptr"))
                    if ptr_files:
                        return (
                            True,
                            f"Staging completed successfully. {len(ptr_files)} files staged for resubmission.",
                            {"staged_files": len(ptr_files)},
                        )

                    # No changes and no .ptr files
                    return (
                        False,
                        "No changes found. Run 'vcp model stage' to stage files for resubmission.",
                        {},
                    )
            except Exception:
                # If git check fails, fall back to .ptr file validation
                ptr_files = list(model_data_path.rglob("*.ptr"))
                if ptr_files:
                    return (
                        True,
                        f"Staging completed successfully. {len(ptr_files)} files staged for resubmission.",
                        {"staged_files": len(ptr_files)},
                    )

            # If no git changes and no .ptr files, show error
            return (
                False,
                "No staged files found. Run 'vcp model stage' to stage your files for resubmission.",
                {},
            )

        except Exception as e:
            return False, f"Error validating resubmission stage step: {e}", {}

    def _validate_metadata_step(self, work_dir: str) -> Tuple[bool, str, Dict]:
        """Validate that metadata step was completed successfully (includes file editing and format validation)."""
        try:
            # Check if this is a resubmission workflow
            is_valid, _metadata_path, metadata = self._get_cached_validation(work_dir)
            if is_valid and metadata.get("resubmit", False):
                # For resubmission, check if files have been edited
                return self._validate_resubmit_file_editing(work_dir)

            # Original validation logic for initial submissions
            work_path = Path(work_dir)
            metadata_file = work_path / "model_card_docs/model_card_metadata.yaml"

            if not metadata_file.exists():
                return (
                    False,
                    "Make sure you are in the root of your model directory. Please ensure model_card_metadata.yaml exists.",
                    {},
                )

            # Check if key files have been modified (not just template files)
            key_files = [
                "model_card_docs/model_card_metadata.yaml",
                "README.md",
                "requirements.txt",
            ]

            modified_files = []
            for file_path in key_files:
                full_path = work_path / file_path
                if full_path.exists():
                    # Check if file has been modified (basic check)
                    stat = full_path.stat()
                    # If file was modified in last 24 hours, consider it edited

                    if time.time() - stat.st_mtime < 86400:  # 24 hours
                        modified_files.append(file_path)

            if not modified_files:
                return (
                    False,
                    "No key files appear to have been edited. Please edit model metadata, documentation, and configuration files.",
                    {},
                )

            # Basic validation - check if required fields are present

            with open(metadata_file, "r") as f:
                metadata = yaml.safe_load(f)

            required_fields = [
                "model_display_name",
                "model_version",
                "model_description",
            ]
            missing_fields = [
                field for field in required_fields if not metadata.get(field)
            ]

            if missing_fields:
                return (
                    False,
                    f"Missing required metadata fields: {missing_fields}. Please complete the metadata file.",
                    {
                        "missing_fields": missing_fields,
                        "modified_files": modified_files,
                    },
                )

            return (
                True,
                f"Metadata step completed. Modified: {', '.join(modified_files)}. All required fields are present.",
                {"validated_fields": required_fields, "modified_files": modified_files},
            )

        except Exception as e:
            return False, f"Error validating metadata step: {e}", {}

    def _validate_copy_weights_step(self, work_dir: str) -> Tuple[bool, str, Dict]:
        """Validate that copy weights step was completed successfully."""
        try:
            work_path = Path(work_dir)

            # Find mlflow package directory
            # TODO: remove wildcard from mlflow_pkg. Unnecessary and only used for backwards compatibility with testing repos
            mlflow_dirs = list(work_path.glob("*mlflow_pkg"))
            if not mlflow_dirs:
                return (
                    False,
                    "No *mlflow_pkg directory found. Please run model packaging first.",
                    {},
                )

            mlflow_dir = mlflow_dirs[0]
            model_data_path = mlflow_dir / "model_data"

            if not model_data_path.exists():
                return (
                    False,
                    "model_data directory not found. Please create it and copy your model weights.",
                    {},
                )

            # Check if model_data directory is not empty (ignoring .gitkeep files)
            all_items = list(model_data_path.rglob("*"))
            # Filter out .gitkeep files
            non_gitkeep_items = [item for item in all_items if item.name != ".gitkeep"]
            if not non_gitkeep_items:
                return (
                    False,
                    "model_data directory is empty. Please copy your model weights.",
                    {},
                )

            return (
                True,
                "Copy weights step completed. Refer to model packaging documentation to create an MLflow package for your model.",
                {"items_count": len(all_items)},
            )

        except Exception as e:
            return False, f"Error validating copy weights step: {e}", {}

    def _validate_resubmit_file_editing(self, work_dir: str) -> Tuple[bool, str, Dict]:
        """Validate that files have been edited for resubmission."""
        try:
            # For resubmission, we need to check if the user has actually edited files
            is_valid, _metadata_path, metadata = self._get_cached_validation(work_dir)

            if not is_valid:
                return (
                    False,
                    "Run 'vcp model init' first to initialize a model packaging work-dir.",
                    {},
                )

            # Check if files have been modified using silent git operations

            # Change to work directory and run silent git status
            original_cwd = os.getcwd()
            try:
                os.chdir(work_dir)

                # Run git status --porcelain to check for modified files (silent, no logs)
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    # Check if there are any modified files (M = modified, A = added, D = deleted)
                    modified_files = [
                        line
                        for line in result.stdout.strip().split("\n")
                        if line and line[0] in "MAD"
                    ]

                    if modified_files:
                        return (
                            True,
                            f"Model files have been modified for resubmission ({len(modified_files)} files changed).",
                            metadata,
                        )
                    else:
                        return (
                            False,
                            "No files have been modified. Please review and edit your model files before proceeding with resubmission.",
                            metadata,
                        )
                else:
                    # Git status failed, fall back to checking if files_edited flag exists
                    files_edited = metadata.get("files_edited", False)
                    if files_edited:
                        return (
                            True,
                            "Model files have been reviewed and edited for resubmission.",
                            metadata,
                        )
                    else:
                        return (
                            False,
                            "Please review and edit your model files before proceeding with resubmission.",
                            metadata,
                        )

            finally:
                # Always restore original working directory
                os.chdir(original_cwd)

        except Exception as e:
            return False, f"Error validating resubmission metadata step: {e}", {}

    def _validate_package_step(self, work_dir: str) -> Tuple[bool, str, Dict]:
        """Validate that package step was completed successfully (includes package creation and validation)."""
        try:
            work_path = Path(work_dir)

            # Check if mlflow_pkg directory exists
            # TODO: remove wildcard from mlflow_pkg. Unnecessary and only used for backwards compatibility with testing repos
            mlflow_pkg_dirs = list(work_path.glob("*mlflow_pkg"))
            if not mlflow_pkg_dirs:
                return (
                    False,
                    "No *mlflow_pkg directory found. Please run 'vcp model init' first.",
                    {},
                )

            mlflow_pkg_dir = mlflow_pkg_dirs[0]

            # Check if model_data directory exists with weights
            model_data_path = mlflow_pkg_dir / "model_data"
            if not model_data_path.exists():
                return (
                    False,
                    "No model_data directory found. Please copy your model weights first.",
                    {},
                )

            # Check if model_data has actual files (not just .gitkeep)
            all_items = list(model_data_path.rglob("*"))
            non_gitkeep_items = [item for item in all_items if item.name != ".gitkeep"]
            if not non_gitkeep_items:
                return (
                    False,
                    "model_data directory is empty. Please copy your model weights first.",
                    {},
                )

            # Check if mlflow_model_artifact directory exists (indicates packaging was completed)
            mlflow_model_artifact_path = mlflow_pkg_dir / "mlflow_model_artifact"
            if not mlflow_model_artifact_path.exists():
                return (
                    False,
                    "Model weights found. Refer to model packaging documentation to create an MLflow package.",
                    {},
                )

            # Check if there are files in mlflow_model_artifact
            files_in_artifact = list(mlflow_model_artifact_path.rglob("*"))
            if not files_in_artifact:
                return (
                    False,
                    "Package validation failed. No files in mlflow_model_artifact directory.",
                    {},
                )

            return (
                True,
                "Package validation completed successfully. Package is ready for staging.",
                {"validation_passed": True},
            )

        except Exception as e:
            return False, f"Error validating package step: {e}", {}

    def _validate_submit_step(self, work_dir: str) -> Tuple[bool, str, Dict]:
        """Validate that submit step was completed successfully."""
        try:
            work_path = Path(work_dir)

            # Check git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=work_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return False, "Not a git repository or git not available", {}

            # Check if there are uncommitted changes
            if result.stdout.strip():
                # Load metadata to check if this is a resubmission
                metadata_file = work_path / ".model-metadata"
                is_resubmit = False
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                        is_resubmit = metadata.get("resubmit", False)
                    except Exception:
                        pass

                if is_resubmit:
                    return (
                        False,
                        "There are unsubmitted changes. Run 'vcp model submit' to submit your resubmission.",
                        {"uncommitted_files": result.stdout.strip().split("\n")[:10]},
                    )
                else:
                    return (
                        False,
                        "There are unsubmitted changes. Submit your changes before proceeding.",
                        {"uncommitted_files": result.stdout.strip().split("\n")[:10]},
                    )

            # Load metadata
            metadata_file = work_path / ".model-metadata"
            if not metadata_file.exists():
                return (
                    False,
                    "Model configuration file not found. Run 'vcp model init' first.",
                    {},
                )

            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            branch_name = metadata.get("branch_name")
            model_name = metadata.get("model_name")
            model_version = metadata.get("model_version")

            if not all([branch_name, model_name, model_version]):
                return (
                    False,
                    "Incomplete model configuration. Missing required fields.",
                    {},
                )

            # Check multiple indicators of successful submission
            validation_results = {
                "branch_on_remote": False,
                "model_card_exists": False,
                "recent_commits": False,
            }

            # 1. Check if branch exists on remote using GitOperations for proper authentication
            if branch_name and self.config:
                try:
                    # Use GitOperations for authenticated git operations (same as init/submit commands)
                    git_ops = GitOperations(str(work_path), self.config, debug=False)
                    remote_result = git_ops._run_git_command_with_auth(
                        ["git", "ls-remote", "--heads", "origin", branch_name],
                        timeout=10,
                    )

                    if remote_result.returncode == 0 and remote_result.stdout.strip():
                        validation_results["branch_on_remote"] = True
                except (
                    subprocess.TimeoutExpired,
                    subprocess.SubprocessError,
                    Exception,
                ):
                    # If git ls-remote fails, we can't determine if branch exists on remote
                    # This is not a critical failure for workflow validation
                    pass
            elif branch_name:
                # Fallback to simple check if no config available
                try:
                    remote_result = subprocess.run(
                        ["git", "ls-remote", "--heads", "origin", branch_name],
                        cwd=work_path,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if remote_result.returncode == 0 and remote_result.stdout.strip():
                        validation_results["branch_on_remote"] = True
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    pass

            # 2. Check if model card files exist
            model_card_path = work_path / "model_card_docs" / "model_card_metadata.yaml"
            if model_card_path.exists():
                validation_results["model_card_exists"] = True

            # 3. Check for recent commits related to model submission
            try:
                commit_result = subprocess.run(
                    ["git", "log", "--oneline", "-10", "--grep", f"model {model_name}"],
                    cwd=work_path,
                    capture_output=True,
                    text=True,
                )
                if commit_result.returncode == 0 and commit_result.stdout.strip():
                    validation_results["recent_commits"] = True
            except Exception:
                pass  # Ignore commit check errors

            # Determine overall success
            success_count = sum(validation_results.values())
            total_checks = len(validation_results)

            if success_count >= 2:  # At least 2 out of 3 checks should pass
                return (
                    True,
                    f"Submit step completed successfully. {success_count}/{total_checks} validation checks passed.",
                    {
                        "branch_name": branch_name,
                        "model_name": model_name,
                        "model_version": model_version,
                        "validation_results": validation_results,
                    },
                )
            else:
                missing_checks = [k for k, v in validation_results.items() if not v]
                return (
                    False,
                    f"Submit step not completed. Missing: {', '.join(missing_checks)}. Run 'vcp model submit' to complete submission.",
                    {
                        "branch_name": branch_name,
                        "validation_results": validation_results,
                        "missing_checks": missing_checks,
                    },
                )

        except Exception as e:
            return False, f"Error validating submit step: {e}", {}

    def get_workflow_status(self, work_dir: str) -> Dict:
        """Get the current status of the workflow in the given directory."""
        # Clear cache at the beginning of workflow status check
        self._clear_validation_cache()

        workflow_steps = self.get_workflow_steps(work_dir)
        workflow_type = self.get_workflow_type(work_dir)

        status = {
            "work_dir": work_dir,
            "current_step": 0,
            "completed_steps": [],
            "next_step": None,
            "issues": [],
            "recommendations": [],
        }

        # For resubmission workflow, start fresh and only mark steps as completed when actually performed
        if workflow_type == "resubmission":
            # For resubmission, we start from step 1 and show proper progression
            # Only mark steps as completed when they've actually been performed
            for step_num, step_info in workflow_steps.items():
                # Check if this step has actually been performed
                is_valid, message, _details = step_info["validation"](work_dir)
                if is_valid:
                    status["completed_steps"].append(step_num)
                    status["current_step"] = step_num
                    if step_info["next_step"]:
                        status["next_step"] = step_info["next_step"]
                else:
                    # This step hasn't been completed yet
                    status["issues"].append(
                        f"Step {step_num} ({step_info['name']}): {message}"
                    )
                    # Only show command recommendations for steps that actually have corresponding commands
                    if step_info["command"] in ["init", "stage", "submit", "status"]:
                        status["recommendations"].append(
                            f"Run: vcp model {step_info['command']}"
                        )
                    break
        else:
            # Original logic for initial submission workflow
            for step_num, step_info in workflow_steps.items():
                is_valid, message, _details = step_info["validation"](work_dir)

                if is_valid:
                    status["completed_steps"].append(step_num)
                    status["current_step"] = step_num
                    if step_info["next_step"]:
                        status["next_step"] = step_info["next_step"]
                else:
                    if step_num == 1:  # First step not completed
                        status["issues"].append(
                            f"Step {step_num} ({step_info['name']}): {message}"
                        )
                        # Only show command recommendations for steps that actually have corresponding commands
                        if step_info["command"] in [
                            "init",
                            "stage",
                            "submit",
                            "status",
                        ]:
                            status["recommendations"].append(
                                f"Run: vcp model {step_info['command']}"
                            )
                        break
                    else:
                        # Previous steps completed, but this one has issues
                        status["issues"].append(
                            f"Step {step_num} ({step_info['name']}): {message}"
                        )
                        # Only show command recommendations for steps that actually have corresponding commands
                        if step_info["command"] in [
                            "init",
                            "stage",
                            "submit",
                            "status",
                        ]:
                            status["recommendations"].append(
                                f"Run: vcp model {step_info['command']}"
                            )
                        break

        # Check if all steps are completed
        total_steps = len(workflow_steps)
        if len(status["completed_steps"]) == total_steps:
            # All steps completed - clear next_step to indicate completion
            status["next_step"] = None

        return status

    def display_workflow_status(self, work_dir: str):
        """Display the current workflow status in a formatted way."""
        status = self.get_workflow_status(work_dir)
        workflow_steps = self.get_workflow_steps(work_dir)
        workflow_type = self.get_workflow_type(work_dir)

        # Create workflow table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=6)
        table.add_column("Step", style="cyan", width=18)
        table.add_column("Description", width=40)
        table.add_column("Status", width=15)

        # Add workflow type header
        workflow_title = (
            "🔄 Resubmission Workflow"
            if workflow_type == "resubmission"
            else "🚀 Initial Submission Workflow"
        )
        console.print(f"\n[bold blue]{workflow_title}[/bold blue]")

        for step_num, step_info in workflow_steps.items():
            if step_num in status["completed_steps"]:
                status_icon = "✅ Completed"
                status_style = "green"
            elif step_num == status["current_step"] + 1:
                status_icon = "🔄 Next"
                status_style = "yellow"
            else:
                status_icon = "⏳ Pending"
                status_style = "dim"

            table.add_row(
                str(step_num),
                step_info["command"],
                step_info["description"],
                f"[{status_style}]{status_icon}[/{status_style}]",
            )

        console.print("\n[bold blue]VCP Model Workflow Status[/bold blue]")
        console.print(f"Working Directory: {work_dir}")
        console.print(table)

        # Show issues and recommendations
        if status["issues"]:
            console.print("\n[bold red]Issues Found:[/bold red]")
            for issue in status["issues"]:
                console.print(f"  • {issue}")

        if status["recommendations"]:
            console.print("\n[bold green]Recommendations:[/bold green]")
            for rec in status["recommendations"]:
                console.print(f"  • {rec}")

        # Show next steps
        if status["next_step"]:
            next_step_info = workflow_steps[status["current_step"] + 1]
            console.print(
                f"\n[bold blue]Next Step:[/bold blue] {next_step_info['name']}"
            )
            if next_step_info["command"] == "manual_review":
                console.print(
                    "[yellow]Action:[/yellow] Manually review and edit template files, all model_card_files required to be updated"
                )
            elif next_step_info["command"] in ["init", "stage", "submit", "status"]:
                console.print(
                    f"Run: [cyan]vcp model {next_step_info['command']} --work-dir {work_dir}[/cyan]"
                )
            # For steps without commands (metadata, weights, package), don't show a run command
        elif not status["next_step"] and len(status["completed_steps"]) == len(
            workflow_steps
        ):
            console.print(
                "\n[bold green]🎉 Workflow Successfully Completed![/bold green]"
            )
            console.print(
                "All workflow steps have been completed successfully. Your model has been submitted to the Virtual Cells Platform."
            )
            console.print("\n[bold blue]What's Next?[/bold blue]")
            console.print("Your model is currently under review.")
            console.print(
                "\nYou can check the status of your submission at any time by running:"
            )
            console.print("[cyan]vcp model status[/cyan]")

    def get_step_guidance(self, step: str, work_dir: str = None) -> str:
        """Get detailed guidance for a specific workflow step."""
        # Use the appropriate workflow based on work_dir if provided
        if work_dir:
            workflow_steps = self.get_workflow_steps(work_dir)
        else:
            workflow_steps = self.workflow_steps

        step_map = {
            info["command"]: (num, info) for num, info in workflow_steps.items()
        }

        if step not in step_map:
            return f"❌ Unknown step: {step}\n\nAvailable steps: {', '.join(step_map.keys())}"

        step_num, step_info = step_map[step]

        guidance = f"""📖 Step {step_num}: {step_info["name"]}

📝 Description: {step_info["description"]}"""

        # Only show command references for steps that actually have corresponding commands
        if step_info["command"] in ["init", "stage", "submit", "status"]:
            guidance += f"""

💻 Command: vcp model {step_info["command"]}
🎯 With work directory: vcp model {step_info["command"]} --work-dir <your-model-workdir>"""

        guidance += """

🔧 What this step does:"""

        if step == "init":
            guidance += """
  • Creates a new model project structure
  • Sets up template files and documentation
  • Configures git repository and branch
  • Creates model configuration file with project information
  • Prepares the workspace for model development"""
        elif step == "status":
            guidance += """
  • Check the current status of your model submission
  • View submission history and feedback
  • See which submissions are under review
  • Check for unresolved feedback items
  • Monitor the progress of your model submissions"""
        elif step == "metadata":
            guidance += """
  • Manually review and edit template files
  • Edit model_card_metadata.yaml with your model details
  • Update README.md with model description and usage
  • Modify requirements.txt with dependencies
  • Customize any other configuration files
  • Review and update documentation
  • All model_card_files are required to be updated"""
        elif step == "format":
            guidance += """
  • Run dry-run validation of metadata format
  • Check required fields are present and valid
  • Verify model description and version format
  • Ensure all metadata follows VCP standards
  • Fix any validation errors before proceeding"""
        elif step == "copy_weights":
            guidance += """
  • Copy your model weights to model_data directory
  • Ensure all model artifacts are included
  • Organize files in proper directory structure
  • Verify file integrity and completeness
  • Check file sizes and formats"""
        elif step == "package":
            guidance += """
  • Package the model with MLflow format
  • Create MLmodel file with model metadata
  • Generate conda.yaml and python_env.yaml
  • Ensure all dependencies are captured
  • Create proper package structure
  • Validate the complete model package
  • Check package integrity and completeness
  • Verify all required files are present
  • Test package loading and dependencies
  • Ensure package meets VCP requirements"""
        elif step == "stage":
            guidance += """
  • Stage model files to the Virtual Cells Platform
  • Creates .ptr pointer files for staged data
  • Validates file integrity and size
  • Prepares files for submission
  • Runs code quality checks"""
        elif step == "submit":
            guidance += """
  • Validates all previous steps are complete
  • Commits changes to git repository
  • Pushes branch to remote repository
  • Creates pull request for model submission
  • Submits model metadata to VCP Model Hub API"""

        guidance += f"""

✅ Prerequisites: {"None" if step_num == 1 else f"Complete step {step_num - 1} first"}
➡️  Next Step: {step_info["next_step"] if step_info["next_step"] else "Workflow complete"}"""

        return guidance


def get_workflow_assistant(config=None) -> ModelWorkflowAssistant:
    """Get a workflow assistant instance."""
    return ModelWorkflowAssistant(config)
