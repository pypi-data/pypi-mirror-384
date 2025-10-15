from __future__ import annotations
from typing import Protocol, Tuple
from deployman.models import Target
# from deployman.connectors.ssh import SSHConnector


class Connector(Protocol):
    """Protocol for connectors; add new implementations (e.g., k8s) without touching CLI/business logic."""

    def get_target(self) -> Target:
        """Return the Target associated with this connector."""
        return self.t

    def check_available(self) -> Tuple[bool, str]:
        """Return (ok, message). Should be fast and non-destructive."""
        ...

    def exec(self, cmd: str, cwd: str | None = None, env: dict | None = None, timeout: int = 300) -> Tuple[int, str, str]:
        """Execute a command on the remote host. Returns (exit_code, stdout, stderr)."""
        ...

    def put_file(self, local_path: str, remote_path: str, mode: int = 0o644) -> None:
        """Upload a local file to a remote path (creates parent dirs).
        Raises IOError/OSError on failure.
        """
        ...

    def get_file(self, remote_path: str) -> bytes:
        """Download a remote file and return its content as bytes.
        Raises IOError/OSError on failure.
        """
        ...

    def get(remote_path: str, local_path: str) -> None:
        """Download a remote file to a local path (creates parent dirs).
        Raises IOError/OSError on failure.
        """
        ...

    def list_files(self, remote_path: str, recursive: bool = False) -> list[str]:
        """List files in a remote directory. If recursive is True, list all files recursively.
        Returns a list of file paths (strings).
        Raises IOError/OSError on failure.
        """
        ...
