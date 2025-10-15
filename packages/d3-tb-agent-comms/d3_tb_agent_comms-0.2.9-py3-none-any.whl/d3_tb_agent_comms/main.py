# ruff: noqa: N802 - caps in function names
# In this case the caps serve a purpose of decerning verb vs noun
# As in we are not, "getting a ping", we are using a "GET" method called "ping"
from __future__ import annotations

import inspect
import json
from typing import TYPE_CHECKING, Final

import requests

from .custom_types import AgentHandlerException, D3SystemInfo, MachineHealthInfo

if TYPE_CHECKING:
    from logging import Logger

SUCCESS: Final[int] = 200


class AgentHandler:
    """Handles Agent API requests. Automatic retry and JSON encode/decode included"""

    def __init__(self, ip: str, port: int, *, logger: Logger) -> None:
        """CTOR for AgentHandler

        :param ip: the ip of the target TB-Agent
        :param port: the port of the target TB-Agent
        :param logger: a logger instance to use for logging
        """
        self.ip = ip
        self.port = port
        self.logger = logger

        self.version = -1

    def _request_handler(self, data: dict | None = None, timeout: int = 5) -> dict:
        """Helper function for handling all request

        :param data: the data to send to the endpoint
        :param timeout: the timeout for the endpoint

        :return: the decoded JSON returned from the endpoint

        :raises:
        """
        calling_func_name = inspect.stack()[1].function
        split_name = calling_func_name.split("_", 1)
        method, endpoint = split_name[0], split_name[1].replace("_", "-")
        url = f"http://{self.ip}:{self.port}/{endpoint}"
        headers = {"accept": "application/json"}

        attempts = 0
        for _ in range(5):
            attempts += 1
            self.logger.info(f"Attempting #{attempts} call to {endpoint}")

            try:
                if method == "GET":
                    response = requests.get(url=url, headers=headers, timeout=timeout)
                elif method == "POST":
                    response = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=timeout)
                else:
                    raise NameError(
                        f"AgentHandler: Name of calling function did not fit expected format: {calling_func_name}\nThis is a bug with the library"  # noqa: E501
                    )
            except requests.RequestException as e:
                self.logger.error(f"!!!!! Failed to get a response from TB-Agent due to: {e}")
                continue

            if not response.ok:
                self.logger.warning(
                    f"!!! The response from the TB-Agent API was not ok\nCode: {response.status_code}\nResponse text: {response.text}"  # noqa: E501
                )
                continue

            try:
                return json.loads(response.text)
            except ValueError as e:
                self.logger.error(f"!!!!! Failed to decode response from TB-Agent: {e}\nRaw text: {response.text}")
                continue

        raise AgentHandlerException(f"!!!!! Maximum number of attempts to get a response from /{endpoint} reached")

    def RAW_ping(self, timeout: int = 2) -> bool:
        """Raw-er version of `GET_ping` for Agent updater checks

        :return: whether a code 200 came back from the request
        """
        url = f"http://{self.ip}:{self.port}/ping"
        headers = {"accept": "application/json"}
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
        except requests.RequestException:
            return False
        else:
            return response.status_code == SUCCESS

    def GET_ping(self) -> None:
        return self._request_handler()["return"]

    def GET_d3installed(self) -> bool:
        return self._request_handler()["msg"]

    def GET_d3system(self) -> D3SystemInfo:
        body = self._request_handler()
        return D3SystemInfo(
            major=body["major"],
            minor=body["minor"],
            patch=body["patch"],
            build=body["build"],
            branch=body["branch"],
            api_port=body["apiPort"],
        )

    def GET_agent_version(self) -> int:
        return self._request_handler()["version"]

    def GET_running_project(self) -> str:
        return self._request_handler()["projectName"]

    def GET_summarise_machine_health(self) -> MachineHealthInfo:
        body = self._request_handler()
        return MachineHealthInfo(
            revision_number=body["revision number"],
            project_folder_check=body["project folder check"],
            project_folder_shared=body["shared project folder check"],
            is_service_running=body["is d3 service running"],
            is_buddy_running=body["is d3 buddy running"],
            can_see_storage_server=body["can machine see storage server"],
            can_see_teamcity=body["can machine see teamcity"],
        )

    def GET_gpu_vendor(self) -> str:
        return self._request_handler()["gpu_output"]

    def GET_current_os(self) -> str:
        return self._request_handler()["OS"]

    def GET_licence_codes(self) -> str:
        return self._request_handler()["licenceCodes"]

    def POST_restart_local_machine(self, timeout: int = 1) -> str:
        data = {"timeout_duration": timeout}
        return self._request_handler(data)["msg"]

    def POST_download_d3(
        self, revision_number: int, destination: str, timeout: int = 0, download_time: int = 360, host: str = ""
    ) -> str:
        data = {"rev": revision_number, "destination": destination}
        if timeout:
            data["timeout"] = timeout
        if host:
            data["host"] = host
        return self._request_handler(data, timeout=download_time)["msg"]

    def POST_install_d3(self, path: str) -> str:
        data = {"path": path}
        return self._request_handler(data, timeout=15)["taskName"]

    def POST_check_pid(self, pid: int) -> bool:
        data = {"pid": pid}
        return self._request_handler(data)["runnning"]

    def POST_update_agent(self, github_key: str) -> None:
        data = {"githubKey": github_key}
        self._request_handler(data, timeout=25)

    def POST_start_d3_project(self, project_folder: str, project_name: str) -> int:
        data = {"projectFolder": project_folder, "projectName": project_name}
        return self._request_handler(data)["msg"]

    def POST_terminate_d3(self) -> str:
        return self._request_handler({})["msg"]

    def POST_delete_d3_installer(self, installer_path: str) -> str:
        data = {"path": installer_path}
        return self._request_handler(data)["msg"]

    def POST_check_task_running(self, task_name: str) -> bool:
        data = {"taskName": task_name}
        return self._request_handler(data, timeout=15)["isRunning"]

    def POST_restart_d3service(self) -> str:
        return self._request_handler()["msg"]
