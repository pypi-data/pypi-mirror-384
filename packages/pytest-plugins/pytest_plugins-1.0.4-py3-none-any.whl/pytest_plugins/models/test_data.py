from dataclasses import dataclass

from pytest_plugins.models.status import ExecutionStatus


@dataclass
class TestData:
    test_file_name: str
    class_test_name: str
    test_name: str
    pytest_test_name: str
    test_full_name: str
    test_full_path: str
    test_status: ExecutionStatus = ExecutionStatus.COLLECTED
    test_parameters: dict[str, str] | None = None
    test_markers: list | None = None
    test_start_time: str | None = None
    test_end_time: str | None = None
    test_duration_sec: float | None = None  # only for the tst itself, not including fixtures
    exception_message: str | None = None
    run_index: int | None = None
