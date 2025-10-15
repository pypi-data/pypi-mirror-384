from dataclasses import dataclass

from pytest_plugins.models.status import ExecutionStatus


@dataclass
class ExecutionData:
    execution_status: ExecutionStatus
    revision: str | None
    execution_start_time: str | None = None
    execution_end_time: str | None = None
    execution_duration_sec: str | None = None

    repo_name: str | None = None
    pull_request_number: str | None = None
    merge_request_number: str | None = None
    pipeline_number: str | None = None
    commit: str | None = None

    test_list: list | None = None
