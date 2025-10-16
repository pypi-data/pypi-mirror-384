# Copyright (C) 2025 Embedl AB


from embedl_hub.tracking.client import Client as _Client
from embedl_hub.tracking.rest_api import RunType

global_client = _Client()

set_project = global_client.set_project
set_experiment = global_client.set_experiment
start_run = global_client.start_run
log_param = global_client.log_param
log_metric = global_client.log_metric


__all__ = [
    "set_project",
    "set_experiment",
    "start_run",
    "log_param",
    "log_metric",
    "RunType",
    "global_client",
]
