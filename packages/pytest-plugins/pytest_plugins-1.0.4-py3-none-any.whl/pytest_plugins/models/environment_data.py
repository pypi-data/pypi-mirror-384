from dataclasses import dataclass


@dataclass
class EnvironmentData:
    python_version: str | None
    platform: str | None
