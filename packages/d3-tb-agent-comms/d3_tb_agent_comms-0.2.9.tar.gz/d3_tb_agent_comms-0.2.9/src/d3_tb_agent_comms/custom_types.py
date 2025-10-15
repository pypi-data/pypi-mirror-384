from dataclasses import dataclass
from typing import final


@final
@dataclass(slots=True)
class D3SystemInfo:
    major: int = 0
    minor: int = 0
    patch: int = 0
    build: int = 0
    branch: str = ""
    api_port: int = 0


@final
@dataclass(slots=True)
class MachineHealthInfo:
    revision_number: int = 0
    project_folder_check: bool = False
    project_folder_shared: bool = False
    is_service_running: bool = False
    is_buddy_running: bool = False
    can_see_storage_server: bool = False
    can_see_teamcity: bool = False


class AgentHandlerException(Exception):
    pass
