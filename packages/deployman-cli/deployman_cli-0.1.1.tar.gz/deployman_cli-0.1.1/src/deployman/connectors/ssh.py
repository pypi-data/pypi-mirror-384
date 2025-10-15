from __future__ import annotations
import os
import socket
import posixpath
import stat
from typing import Tuple, Optional
import paramiko
# from deployman.connectors.base import Connector
from deployman.connectors.base import Connector
from deployman.models import Target


class SSHConnector(Connector):
    def __init__(self, target: Target) -> None:
        if not target.ssh:
            raise ValueError("SSHConnector requires target.ssh to be set")
        self.t = target
        self._client: Optional[paramiko.SSHClient] = None

    # --------------- lifecycle ---------------
    def _client_connected(self) -> paramiko.SSHClient:
        if self._client:
            return self._client
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(
            hostname=self.t.ssh.host,
            port=self.t.ssh.port,
            username=self.t.ssh.username,
            key_filename=self.t.ssh.key_path,
            timeout=15,
        )
        self._client = c
        return c

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    # --------------- simple checks ---------------
    def check_available(self) -> Tuple[bool, str]:
        # 1) TCP reachability
        try:
            with socket.create_connection((self.t.ssh.host, self.t.ssh.port), timeout=5):
                pass
        except Exception as e:
            return False, f"TCP {self.t.ssh.host}:{self.t.ssh.port} not reachable: {e}"

        # 2) SSH sanity command
        try:
            client = self._client_connected()
            stdin, stdout, stderr = client.exec_command("echo ok", timeout=10)
            if stdout.read().decode().strip() == "ok":
                return True, "SSH reachable"
            return False, "SSH command failed"
        except Exception as e:
            return False, f"SSH handshake/command failed: {e}"

    # --------------- exec & file ops ---------------
    def exec(self, cmd: str, cwd: Optional[str] = None, env: Optional[dict] = None, timeout: int = 300):
        """Execute a command on the remote host. Returns (exit_code, stdout, stderr)."""
        client = self._client_connected()
        if cwd:
            cmd = f"cd {cwd} && " + cmd
        if env:
            env_str = " ".join([f"{k}='{v}'" for k, v in env.items()])
            cmd = f"export {env_str} && " + cmd
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        code = stdout.channel.recv_exit_status()
        return code, out, err

    def put_bytes(self, data: bytes, remote_path: str, mode: int = 0o644) -> None:
        client = self._client_connected()
        sftp = client.open_sftp()
        # ensure parent dirs
        parent = posixpath.dirname(remote_path)
        self._mkdirs(sftp, parent)
        with sftp.open(remote_path, "wb") as f:
            f.write(data)
        sftp.chmod(remote_path, mode)
        sftp.close()

    def put_file(self, local_path: str, remote_path: str, mode: int = 0o644) -> None:
        """Upload a local file to a remote path (creates parent dirs).
        Raises IOError/OSError on failure.
        """
        client = self._client_connected()
        sftp = client.open_sftp()
        # ensure parent dirs
        parent = posixpath.dirname(remote_path)
        self._mkdirs(sftp, parent)
        sftp.put(local_path, remote_path)
        sftp.chmod(remote_path, mode)
        sftp.close()

    def get_file(self, remote_path: str, local_path: str) -> None:
        """Download a remote file to a local path (creates parent dirs).
        Raises IOError/OSError on failure.
        """
        client = self._client_connected()
        sftp = client.open_sftp()
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        sftp.get(remote_path, local_path)
        sftp.close()

    def list_files(self, remote_path: str, recursive: bool = False) -> list[str]:
        """List files in a remote directory. If recursive is True, lists all files recursively."""
        client = self._client_connected()
        sftp = client.open_sftp()
        files = []

        def _list_dir(rpath: str) -> None:
            for entry in sftp.listdir_attr(rpath):
                full_path = posixpath.join(rpath, entry.filename)
                if stat.S_ISDIR(entry.st_mode):
                    if recursive:
                        _list_dir(full_path)
                else:
                    files.append(full_path)

        _list_dir(remote_path)
        sftp.close()
        return files

    def get(self, remote_path: str, local_path: str) -> None:
        """Download a file or a directory (recursively) preserving structure.

        Behaviour:
        - If `remote_path` is a FILE:
            * If `local_path` is an existing directory (or ends with a path separator),
              the file will be saved as `local_path/<basename(remote_path)>`.
            * Otherwise it is treated as the full destination filename.
        - If `remote_path` is a DIRECTORY:
            * Its *basename* will be created under `local_path`, then contents
              mirrored recursively: `local_path/<basename(remote_path)>/**`.
        """
        client = self._client_connected()
        sftp = client.open_sftp()

        def _is_dir(rp: str) -> bool:
            try:
                st = sftp.stat(rp)
                return stat.S_ISDIR(st.st_mode)
            except IOError:
                return False

        def _download_dir(rdir: str, ldir: str) -> None:
            os.makedirs(ldir, exist_ok=True)
            for entry in sftp.listdir_attr(rdir):
                r_child = posixpath.join(rdir, entry.filename)
                l_child = os.path.join(ldir, entry.filename)
                if stat.S_ISDIR(entry.st_mode):
                    _download_dir(r_child, l_child)
                else:
                    os.makedirs(os.path.dirname(l_child) or ".", exist_ok=True)
                    sftp.get(r_child, l_child)

        try:
            if _is_dir(remote_path):
                base = posixpath.basename(remote_path.rstrip('/')) or "root"
                root_local = os.path.join(local_path, base)
                _download_dir(remote_path, root_local)
            else:
                dest = local_path
                # If local_path is an existing directory or endswith separator, place inside
                if (os.path.isdir(local_path)) or local_path.endswith((os.sep, "/")):
                    dest = os.path.join(local_path, os.path.basename(remote_path))
                os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
                sftp.get(remote_path, dest)
        finally:
            sftp.close()

    def _mkdirs(self, sftp: paramiko.SFTPClient, path: str) -> None:
        parts = []
        p = path
        while p not in ("/", ""):
            parts.append(p)
            p = posixpath.dirname(p)
        for d in reversed(parts):
            try:
                sftp.stat(d)
            except IOError:
                sftp.mkdir(d)