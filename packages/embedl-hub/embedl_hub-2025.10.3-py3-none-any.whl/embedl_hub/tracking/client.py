# Copyright (C) 2025 Embedl AB

import os
from contextlib import contextmanager
from datetime import datetime, timezone

from embedl_hub.core.context import read_embedl_hub_context
from embedl_hub.tracking.rest_api import (
    ApiConfig,
    CompletedRunStatus,
    Experiment,
    Metric,
    Parameter,
    Project,
    Run,
    RunStatus,
    RunType,
    create_experiment,
    create_project,
    create_run,
    get_experiment_by_name,
    get_project_by_name,
    log_metric,
    log_param,
    update_run,
)

API_KEY_ENV_VAR_NAME = "EMBEDL_HUB_API_KEY"
BASE_URL_ENV_VAR_NAME = "EMBEDL_HUB_API_BASE_URL"

DEFAULT_API_BASE_URL = "https://hub.embedl.com/"


class Client:
    """Tracks projects, experiments and runs for the Embedl Hub web app."""

    _api_config: ApiConfig | None
    _project: Project | None
    _experiment: Experiment | None
    _active_run: Run | None

    def __init__(self, api_config: ApiConfig | None = None) -> None:
        self._api_config = api_config
        self._project = None
        self._experiment = None
        self._active_run = None

    def set_project(self, name: str) -> Project:
        """Set or create the current project by name."""

        project = get_project_by_name(self.api_config, name)

        if not project:
            project = create_project(self.api_config, name)

        self._project = project

        return project

    def set_experiment(self, name: str) -> Experiment:
        """Set or create the current experiment by name."""

        project_id = self.project.id
        experiment = get_experiment_by_name(self.api_config, name, project_id)

        if not experiment:
            experiment = create_experiment(self.api_config, name, project_id)

        self._experiment = experiment

        return experiment

    def create_run(self, type: RunType, name: str | None = None) -> Run:
        """Create a new run for the current project and experiment."""

        project = self.project
        experiment = self.experiment

        run = create_run(
            self.api_config,
            type=type,
            name=name,
            started_at=datetime.now(timezone.utc),
            project_id=project.id,
            experiment_id=experiment.id,
        )

        return run

    def update_active_run(
        self, status: CompletedRunStatus, ended_at: datetime
    ) -> None:
        """Update the status and end time of the active run."""

        project = self.project
        experiment = self.experiment
        run = self.active_run

        update_run(
            self.api_config,
            status=status,
            ended_at=ended_at,
            project_id=project.id,
            experiment_id=experiment.id,
            run_id=run.id,
        )

    @contextmanager
    def start_run(self, type: RunType, name: str | None = None):
        """Context manager to start and finish a run."""

        run = self.create_run(type, name)
        self._active_run = run

        status: CompletedRunStatus = RunStatus.FINISHED

        try:
            yield run
        except KeyboardInterrupt:
            status = RunStatus.KILLED
            raise
        except Exception:
            status = RunStatus.FAILED
            raise
        finally:
            self.update_active_run(
                status=status, ended_at=datetime.now(timezone.utc)
            )
            self._active_run = None

    def log_param(self, name: str, value: str) -> Parameter:
        """Log a parameter for the current run."""

        project = self.project
        experiment = self.experiment
        active_run = self.active_run

        param = log_param(
            self.api_config,
            name=name,
            value=value,
            project_id=project.id,
            experiment_id=experiment.id,
            run_id=active_run.id,
        )

        return param

    def log_metric(
        self, name: str, value: float, step: int | None = None
    ) -> Metric:
        """Log a metric for the current run."""

        project = self.project
        experiment = self.experiment
        active_run = self.active_run

        metric = log_metric(
            self.api_config,
            name=name,
            value=value,
            step=step,
            project_id=project.id,
            experiment_id=experiment.id,
            run_id=active_run.id,
        )

        return metric

    @property
    def api_config(self) -> ApiConfig:
        """Get or create the API config from environment variables."""

        if self._api_config is None:
            # environment variable takes precedence over context
            def get_api_key() -> str | None:
                """Get API key from environment or context."""
                if key := os.getenv(API_KEY_ENV_VAR_NAME):
                    return key
                return read_embedl_hub_context().get("api_key")

            if api_key := get_api_key():
                api_base_url = os.getenv(
                    BASE_URL_ENV_VAR_NAME, DEFAULT_API_BASE_URL
                )
                self._api_config = ApiConfig(
                    api_key=api_key, base_url=api_base_url
                )
            else:
                raise RuntimeError(
                    "No API key found. "
                    f"{API_KEY_ENV_VAR_NAME} must be set or stored in context by running `embedl-hub auth --api-key`."
                )

        return self._api_config

    @property
    def project(self) -> Project:
        if self._project is None:
            raise RuntimeError("Project is not set. Use set_project() first.")

        return self._project

    @property
    def experiment(self) -> Experiment:
        if self._experiment is None:
            raise RuntimeError(
                "Experiment is not set. Use set_experiment() first."
            )

        return self._experiment

    @property
    def active_run(self) -> Run:
        if self._active_run is None:
            raise RuntimeError(
                "There is no active run. Use start_run() as a context manager first."
            )

        return self._active_run
