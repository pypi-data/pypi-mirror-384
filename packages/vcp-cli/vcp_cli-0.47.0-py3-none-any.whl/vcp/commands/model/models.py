"""Pydantic models for Model Hub API responses."""

from typing import Literal

from pydantic import BaseModel


class ModelVersionResponse(BaseModel):
    """
    Model version information.

    Attributes:
        version: Version identifier (e.g., '1.0.0', 'v2')
        description: Human-readable description of this version
    """

    version: str
    description: str


class ModelResponse(BaseModel):
    """
    Model information from Model Hub.

    Attributes:
        name: Model name
        versions: List of available versions for this model
    """

    name: str
    versions: list[ModelVersionResponse]


class ModelsListResponse(BaseModel):
    """
    Response from GET /api/models/list.

    Attributes:
        models: List of available models with their versions
    """

    models: list[ModelResponse]


class SubmissionData(BaseModel):
    """
    Submission information from Model Hub API.

    Attributes:
        submission_id: Unique identifier for the submission
        model_name: Name of the model
        model_version: Version of the model
        repo_url: GitHub repository URL for the submission
        status: Current status of the submission
    """

    submission_id: str
    model_name: str
    model_version: str
    repo_url: str
    status: Literal[
        "initialized",
        "submitted",
        "submitted_changes_requested",
        "ready_for_processing",
        "processing_failed",
        "processed",
        "metadata_changes_requested",
        "accepted",
        "denied",
    ]


class SubmissionResponse(BaseModel):
    """
    Response from POST /api/sub.

    Attributes:
        submission: Submission data including repo URL and submission ID
    """

    submission: SubmissionData
