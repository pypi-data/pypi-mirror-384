# Copyright (C) 2025 Embedl AB

"""
Utils for Qualcomm AI Hub integration.
"""

import qai_hub as hub
import qai_hub.public_api_pb2 as hub_pb
import qai_hub.public_rest_api as hub_api
from qai_hub.client import Client
from qai_hub.hub import _global_client

QAI_HUB_RUNTIME_NAMES = ["ONNX Runtime", "TensorFlow Lite", "QNN"]


def get_global_qai_hub_client() -> Client:
    """Get the global Qualcomm AI Hub API client."""
    return _global_client


def get_job_result(
    job_id: str, client_config: hub_api.ClientConfig
) -> hub_pb.JobResult:
    """Get the protobuf representation of a job result from Qualcomm AI Hub.

    Used to retrieve information about a job that is otherwise not exposed by
    the `qai_hub` package.
    """
    # pylint: disable-next=protected-access
    job_result: hub_pb.JobResult = hub.client._api_call(
        hub_api.get_job_results, client_config, job_id
    )
    return job_result


def parse_runtime_info(job_result: hub_pb.JobResult) -> str:
    """Extract the runtime name from job result protobuf.

    If no recognized runtime is found, an error will be raised.
    """

    runtime = None

    job_type = job_result.WhichOneof("result")

    job_runtime_names = []

    if job_type == "compile_job_result":
        job_runtime_names = [
            tool.name
            for tool in job_result.compile_job_result.compile_detail.tool_versions
        ]
    elif job_type == "profile_job_result":
        job_runtime_names = [
            runtime.name
            for runtime in job_result.profile_job_result.profile.runtime_config
        ]
    else:
        raise RuntimeError(f"Unrecognized job type: {job_type}.")

    for expected_runtime_name in QAI_HUB_RUNTIME_NAMES:
        if expected_runtime_name in job_runtime_names:
            runtime = expected_runtime_name
            break

    if runtime is None:
        raise RuntimeError(
            f"No recognized runtime in job result: {job_runtime_names}. "
            f"Expected one of: {QAI_HUB_RUNTIME_NAMES}."
        )

    return runtime
