# Copyright (C) 2025 Embedl AB

import os
from datetime import datetime, timezone
from urllib.parse import urljoin

from embedl_hub.tracking.client import (
    BASE_URL_ENV_VAR_NAME,
    DEFAULT_API_BASE_URL,
)
from embedl_hub.tracking.rest_api import Experiment, Project, Run


def to_project_url(project_id: str):
    """Convert a Project object to its URL representation."""
    base_url = os.getenv(BASE_URL_ENV_VAR_NAME, DEFAULT_API_BASE_URL)

    return urljoin(base_url, f"projects/{project_id}")


def to_experiment_url(project_id: str, experiment_id: str):
    """Convert an Experiment object to its URL representation."""
    base_url = os.getenv(BASE_URL_ENV_VAR_NAME, DEFAULT_API_BASE_URL)
    return urljoin(
        base_url, f"projects/{project_id}/experiments/{experiment_id}"
    )


def to_run_url(project_id: str, experiment_id: str, run_id: str):
    """Convert a Run object to its URL representation."""
    base_url = os.getenv(BASE_URL_ENV_VAR_NAME, DEFAULT_API_BASE_URL)
    return urljoin(
        base_url,
        f"projects/{project_id}/experiments/{experiment_id}/runs/{run_id}",
    )


def timestamp_id(prefix: str) -> str:
    """Generate a unique random name based on timestamp."""
    return (
        f"{prefix}_{datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    )
