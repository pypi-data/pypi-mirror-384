# Copyright (C) 2025 Embedl AB

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Self, TypeAlias
from urllib.parse import urljoin

import requests
from pydantic import BaseModel
from pydantic.alias_generators import to_camel


@dataclass
class ApiConfig:
    """Configuration for interacting with the Embedl Hub REST API."""

    base_url: str
    api_key: str

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }


class Model(BaseModel):
    """Base model with camel case aliasing."""

    class Config:
        alias_generator = to_camel
        validate_by_name = True


class Project(Model):
    id: str
    name: str


class Experiment(Model):
    id: str
    name: str


class RunType(Enum):
    QUANTIZE = "QUANTIZE"
    COMPILE = "COMPILE"
    BENCHMARK = "BENCHMARK"


class RunStatus(Enum):
    RUNNING = "RUNNING"
    SCHEDULED = "SCHEDULED"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    KILLED = "KILLED"


class Run(Model):
    id: str
    name: str
    type: RunType
    status: RunStatus
    created_at: datetime
    started_at: datetime
    ended_at: datetime | None


class Parameter(Model):
    name: str
    value: str
    measured_at: datetime


class Metric(Model):
    name: str
    value: float
    step: int
    measured_at: datetime


CompletedRunStatus: TypeAlias = Literal[
    RunStatus.FINISHED, RunStatus.KILLED, RunStatus.FAILED
]


JSONObj: TypeAlias = Dict[str, Any]
JSONItems: TypeAlias = List[JSONObj]
JSONData: TypeAlias = JSONObj | JSONItems


def create_project(config: ApiConfig, name: str) -> Project:
    """Create a new project."""

    data = _request(config, "POST", "/api/projects", json={"name": name})

    data = _expect_dict(data)

    return Project(**data)


def get_project_by_name(config: ApiConfig, name: str) -> Project | None:
    """Get project by name, or None if not found."""

    try:
        data = _request(
            config,
            "GET",
            "/api/projects",
            params={"name": name},
        )
    except ApiError as err:
        if err.status_code == 404:
            return None
        raise

    data = _expect_dict(data)

    return Project(**data)


def create_experiment(
    config: ApiConfig, name: str, project_id: str
) -> Experiment:
    """Create a new experiment."""

    data = _request(
        config,
        "POST",
        f"/api/projects/{project_id}/experiments",
        json={"name": name},
    )

    data = _expect_dict(data)

    return Experiment(**data)


def get_experiment_by_name(
    config: ApiConfig, name: str, project_id: str
) -> Experiment | None:
    """Get experiment by name, or None if not found."""

    try:
        data = _request(
            config,
            "GET",
            f"/api/projects/{project_id}/experiments",
            params={"name": name},
        )
    except ApiError as err:
        if err.status_code == 404:
            return None
        raise

    data = _expect_dict(data)

    return Experiment(**data)


def create_run(
    config: ApiConfig,
    project_id: str,
    experiment_id: str,
    type: RunType,
    started_at: datetime,
    name: str | None = None,
) -> Run:
    """Create a new run."""

    payload = {"type": type.value}
    if name:
        payload["name"] = name
    payload["startedAt"] = started_at.isoformat()

    data = _request(
        config,
        "POST",
        f"/api/projects/{project_id}/experiments/{experiment_id}/runs",
        json=payload,
    )

    data = _expect_dict(data)

    return Run(**data)


def update_run(
    config: ApiConfig,
    project_id: str,
    experiment_id: str,
    run_id: str,
    status: CompletedRunStatus,
    ended_at: datetime,
) -> None:
    """Update run status and end time."""

    _request(
        config,
        "PATCH",
        f"/api/projects/{project_id}/experiments/{experiment_id}/runs/{run_id}",
        json={"status": status.value, "endedAt": ended_at.isoformat()},
    )


def log_param(
    config: ApiConfig,
    name: str,
    value: str,
    project_id: str,
    experiment_id: str,
    run_id: str,
) -> Parameter:
    """Log a parameter for a run."""

    payload = {"name": name, "value": value}
    data = _request(
        config,
        "POST",
        f"/api/projects/{project_id}/experiments/{experiment_id}/runs/{run_id}/params",
        json=payload,
    )

    data = _expect_dict(data)

    return Parameter(**data)


def log_metric(
    config: ApiConfig,
    name: str,
    value: float,
    project_id: str,
    experiment_id: str,
    run_id: str,
    step: int | None = None,
) -> Metric:
    """Log a metric for a run."""

    payload = {"name": name, "value": value}
    if step is not None:
        payload["step"] = step

    data = _request(
        config,
        "POST",
        f"/api/projects/{project_id}/experiments/{experiment_id}/runs/{run_id}/metrics",
        json=payload,
    )

    data = _expect_dict(data)

    return Metric(**data)


def _expect_dict(data: JSONData | None) -> JSONObj:
    """Ensure data is a dict, else raise error."""

    if not isinstance(data, dict):
        raise RuntimeError("Unexpected response shape: expected object")
    return data


def _request(
    config: ApiConfig,
    method: str,
    url: str,
    json: JSONObj | None = None,
    params: Dict[str, str | int] | None = None,
) -> JSONData | None:
    """Send HTTP request and handle API response."""

    full_url = urljoin(config.base_url, url)

    try:
        resp = requests.request(
            method=method,
            url=full_url,
            headers=config.headers,
            json=json,
            params=params,
            timeout=10,
        )
    except requests.exceptions.RequestException as exc:
        raise NetworkRequestError(
            f"Request to {full_url} failed: {exc}"
        ) from exc

    try:
        payload: JSONObj = resp.json() if resp.content else {}
    except ValueError:
        payload = {}

    if resp.ok:
        if resp.status_code == 204:
            return None

        if "data" in payload:
            return payload["data"]

        raise ApiError(resp.status_code, "Missing `data` field", [], resp)

    errors = [
        ApiErrorDetail.from_dict(err) for err in payload.get("errors", [])
    ]
    message = payload.get("message") or resp.reason
    raise ApiError(resp.status_code, message, errors, resp)


@dataclass
class ApiErrorDetail:
    """An individual error contained in an API error response."""

    title: str | None = None
    status: int | None = None
    code: str | None = None
    detail: str | None = None
    source: dict[str, str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            title=data.get("title"),
            status=data.get("status"),
            code=data.get("code"),
            detail=data.get("detail"),
            source=data.get("source"),
        )

    def __str__(self) -> str:
        parts: list[str] = []
        if self.title:
            parts.append(self.title)
        if self.code:
            parts.append(f"(code: {self.code})")
        if self.status:
            parts.append(f"[{self.status}]")
        if self.detail:
            parts.append(self.detail)
        if self.source:
            parts.append(f"-> {self.source}")
        return " ".join(parts) or "<empty>"


class ApiError(Exception):
    """Raised for API errors with JSON body."""

    def __init__(
        self,
        status_code: int,
        message: str,
        errors: list[ApiErrorDetail] | None = None,
        response: requests.Response | None = None,
    ) -> None:
        super().__init__(f"{status_code} {message}")
        self.status_code = status_code
        self.message = message
        self.errors = errors or []
        self.response = response

    def __str__(self) -> str:
        if not self.errors:
            return super().__str__()
        joined = "\n".join(map(str, self.errors))
        return f"{super().__str__()}\n{joined}"


class NetworkRequestError(Exception):
    """Raised when HTTP request fails."""
