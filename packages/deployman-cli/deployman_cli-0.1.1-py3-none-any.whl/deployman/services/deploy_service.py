from __future__ import annotations

from pydantic_core import ValidationError
from deployman.connectors import ConnectorFactory
from deployman.services.service import ServiceLoader
from deployman.storage import ConfigRepository
from deployman.deployers.compose_deployer import ComposeDeployer
from deployman.services.targets_service import TargetsService


class DeployService:
    """High-level deployment entrypoints used by the CLI."""

    def __init__(self, repo: ConfigRepository | None = None) -> None:
        self.repo = repo or ConfigRepository()

    def deploy(self, service_file: str, target_name: str) -> str:
        try:
            service = ServiceLoader.load_service(service_file)
        except ValidationError as e:
            return f"[red]ERROR[/red] Failed to load service file '{service_file}': {e}"

        target = TargetsService(self.repo).load_target(target_name or service.target)

        if service is None:
            return f"[red]ERROR[/red] Service file '{service_file}' could not be loaded"

        if target is None:
            return f"[red]ERROR[/red] Target '{target_name}' not found"

        connection = ConnectorFactory.create(target)

        if service.method == "compose":
            ok, msg = ComposeDeployer(self.repo, connection=connection).deploy(service, start=True)
        else:
            ok, msg = False, f"Unsupported service method: {service.method}"

        return ("[green]SUCCESS[/green] " + msg) if ok else ("[red]ERROR[/red] " + msg)

    def remove(self, service_file: str) -> str:
        try:
            service = ServiceLoader.load_service(service_file)
        except ValidationError as e:
            return f"[red]ERROR[/red] Failed to load service file '{service_file}': {e}"

        target = TargetsService(self.repo).load_target(service.target)

        if service is None:
            return f"[red]ERROR[/red] Service file '{service_file}' could not be loaded"

        if target is None:
            return f"[red]ERROR[/red] Target '{service.target}' not found"

        connection = ConnectorFactory.create(target)

        if service.method == "compose":
            ok, msg = ComposeDeployer(self.repo, connection=connection).remove(service)
        else:
            ok, msg = False, f"Unsupported service method: {service.method}"

        return ("[green]SUCCESS[/green] " + msg) if ok else ("[red]ERROR[/red] " + msg)