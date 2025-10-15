from __future__ import annotations
from typing import Tuple, List
import json
from rich.console import Console

from deployman.connectors.base import Connector
from deployman.models import Service
from deployman.services.service import ServicePathResolver
from deployman.storage import ConfigRepository

class ComposeServiceContainer:
    exit_code: int
    health: str
    id: str
    name: str
    service: str
    state: str


class ComposeDeployer:
    def __init__(self, repo: ConfigRepository | None = None, connection: Connector | None = None) -> None:
        self.repo = repo or ConfigRepository()
        self.connection = connection
        self.console = Console()

    def _compose_pull(self, service_name: str, connection: Connector, compose_path: str, env: dict[str, str]) -> Tuple[bool, str]:
        pull_cmd = f"docker compose -p {service_name} -f {compose_path} pull"
        self.console.log(f"Executing: {pull_cmd}")
        code, out, err = connection.exec(pull_cmd, env=env)
        if code != 0:
            return False, f"Compose pull failed: {err or out}"
        return True, "Compose pull succeeded"

    def _compose_up(self, service_name: str, connection: Connector, compose_path: str, env: dict[str, str]) -> Tuple[bool, str]:
        up_cmd = f"docker compose -p {service_name} -f {compose_path} up -d --force-recreate --remove-orphans"
        self.console.log(f"Executing: {up_cmd}")
        self.console.log(f"      env: {env}")
        code, out, err = connection.exec(up_cmd, env=env)
        if code != 0:
            return False, f"Compose up failed: {err or out}"
        return True, "Compose up succeeded"

    def _upload_file(self, local_path: str, remote_path: str, mode: int) -> None:
        self.console.log(f"Uploading: {local_path} -> {remote_path}")
        try:
            self.connection.put_file(local_path, remote_path, mode)
            return True
        except FileNotFoundError as e:
            self.console.log(f"Local file not found: {e}")
            return False

    def deploy(self, service: Service, start: bool = True) -> Tuple[bool, str]:
        self.console.log(f"Deploying service '{service.name}' to target '{self.connection.t.name}'")

        _compose_local_path = ServicePathResolver.resolve_local_compose_file(service)
        _compose_remote_path = ServicePathResolver.resolve_remote_compose_file(service, self.connection)

        if not self._upload_file(_compose_local_path, _compose_remote_path, 0o644):
            return False, f"Local compose file not found: {_compose_local_path}"

        for file in service.compose.additional_files:
            _local_file = ServicePathResolver.resolve_local_rel_path(service, file.src)
            _remote_file = ServicePathResolver.resolve_remote_rel_config_path(service, self.connection.get_target(), file.src or file.dest)

            if not self._upload_file(_local_file, _remote_file, int(file.mode, 8)):
                return False, f"Local additional file not found: {file.src}"

        _env = {
            "deployman_service_data_dir": ServicePathResolver.resolve_remote_data_dir(service, self.connection.get_target()),
        }

        ok, msg = self._compose_pull(service.name, self.connection, _compose_remote_path, _env)
        if not ok:
            return False, msg
        if start:
            ok, msg = self._compose_up(service.name, self.connection, _compose_remote_path, _env)
            if not ok:
                return False, msg

        return True, f"Service '{service.name}' deployed to {self.connection.t.name}"

    def remove(self, service: Service) -> Tuple[bool, str]:
        self.console.log(f"Removing service '{service.name}' from target '{self.connection.t.name}'")

        _compose_remote_path = ServicePathResolver.resolve_remote_compose_file(service, self.connection)

        _env = {
                "deployman_service_data_dir": ServicePathResolver.resolve_remote_data_dir(service, self.connection.get_target()),
        }

        down_cmd = f"docker compose -p {service.name} -f {_compose_remote_path} down --volumes --remove-orphans"
        self.console.log(f"Executing: {down_cmd}")
        code, out, err = self.connection.exec(down_cmd, env=_env)
        if code != 0:
            return False, f"Compose down failed: {err or out}"

        return True, f"Service '{service.name}' removed from {self.connection.t.name}"

    def list_containers(self, service: Service) -> Tuple[bool, List[str] | str]:
        self.console.log(f"Listing containers for service '{service.name}' on target '{self.connection.t.name}'")

        _compose_remote_path = ServicePathResolver.resolve_remote_compose_file(service, self.connection)

        ps_cmd = f"docker compose -p {service.name} -f {_compose_remote_path} ps -aq"
        self.console.log(f"Executing: {ps_cmd}")
        code, out, err = self.connection.exec(ps_cmd)
        if code != 0:
            return False, f"Compose ps failed: {err or out}"

        try:
            containers = json.loads(out)
            container_list = [
                ComposeServiceContainer(
                    exit_code=c.get("ExitCode", -1),
                    health=c.get("Health"),
                    id=c.get("ID"),
                    name=c.get("Name"),
                    service=c.get("Service"),
                    state=c.get("State"),
                ) for c in containers]
            return True, container_list
        except json.JSONDecodeError as e:
            return False, f"Failed to parse JSON output: {e}"