from pathlib import Path
import yaml
from pydantic import ValidationError

from deployman.connectors.base import Connector
from deployman.models import Service, Target


class ServicePathResolver:
    """Utility class to resolve service-related paths."""

    @staticmethod
    def resolve_remote_config_dir(service: Service, target: Target) -> str:
        """
        Resolve the target config directory for the service on the remote host.
        Args:
            service: Service instance.
            target: Target instance.
        Returns:
            str: Resolved remote config directory path.
        """
        return str(Path(target.compose_config.config_directory, service.name))

    @staticmethod
    def resolve_remote_data_dir(service: Service, target: Target) -> str:
        """
        Resolve the target data directory for the service on the remote host.
        Args:
            service: Service instance.
            target: Target instance.
        Returns:
            str: Resolved remote data directory path.
        """
        return str(Path(target.compose_config.data_directory, service.name))

    @staticmethod
    def resolve_local_rel_path(service: Service, relative_path: str) -> str:
        """
        Resolve a local file path relative to the service's config directory.
        Args:
            service: Service instance.
            relative_path: Relative file path.
        Returns:
            str: Resolved local file path.
        """
        service_dir = Path(service._location).parent
        return str(Path(service_dir, relative_path))

    @staticmethod
    def resolve_remote_rel_config_path(service: Service, target: Target, relative_path: str) -> str:
        """
        Resolve a remote file path relative to the service's config directory on the target host.
        Args:
            service: Service instance.
            target: Target instance.
            relative_path: Relative file path.
        Returns:
            str: Resolved remote file path.
        """
        remote_config_dir = ServicePathResolver.resolve_remote_config_dir(service, target)
        return str(Path(remote_config_dir, relative_path))

    @staticmethod
    def resolve_remote_rel_data_path(service: Service, target: Target, relative_path: str) -> str:
        """
        Resolve a remote file path relative to the service's data directory on the target host.
        Args:
            service: Service instance.
            target: Target instance.
            relative_path: Relative file path.
        Returns:
            str: Resolved remote file path.
        """
        remote_data_dir = ServicePathResolver.resolve_remote_data_dir(service, target)
        return str(Path(remote_data_dir, relative_path))

    @staticmethod
    def resolve_local_compose_file(service: Service) -> str:
        """
        Resolve the local path to the compose file.
        Args:
            service: Service instance.
        Returns:
            str: Resolved local compose file path.
        """
        service_dir = Path(service._location).parent
        return str(Path(service_dir, service.compose.compose_file))

    @staticmethod
    def resolve_remote_compose_file(service: Service, connection: Connector) -> str:
        """
        Resolve the remote path to the compose file on the target host.
        Args:
            service: Service instance.
            connection: Connector instance connected to target host.
        Returns:
            str: Resolved remote compose file path.
        """
        _remote_config_dir = ServicePathResolver.resolve_remote_config_dir(service, connection.get_target())
        return str(Path(_remote_config_dir, service.compose.compose_file))


class ServiceLoader:
    """Utility class to load service specifications from YAML files."""

    @staticmethod
    def load_service(service_file: str) -> Service:
        """Load a service specification from a YAML file.
        Args:
            service_file (str): Path to the service YAML file.
        Returns:
            Service: Loaded Service instance.
        """
        try:
            data = yaml.safe_load(Path(service_file).read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise FileNotFoundError(f"Service file '{service_file}' not found")

        try:
            service = Service.model_validate(data)
            service._location = service_file  # store for internal use
        except ValidationError as e:
            raise ValidationError(f"Failed to validate service file '{service_file}': {e}")

        return service


class ComposeLoader:
    """Utility class to load service compose definition from YAML file."""

    @staticmethod
    def load_compose(compose_file: str) -> dict:
        """Load a service compose definition from a YAML file.
        Args:
            service_file (str): Path to the service YAML file.
        Returns:
            Service: Loaded Service instance.
        """
        try:
            data = yaml.safe_load(Path(compose_file).read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise FileNotFoundError(f"Compose file '{compose_file}' not found")
        finally:
            return data
