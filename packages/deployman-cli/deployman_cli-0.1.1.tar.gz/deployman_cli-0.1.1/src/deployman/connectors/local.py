from __future__ import annotations
import os
import stat
import shutil
import subprocess
from typing import Optional, Tuple

# from deployman.connectors.base import Connector
from deployman.models import Target


class LocalConnector:
    """
    Connector that executes commands and performs file operations on the local host.
    Keeps the same public interface as SSHConnector for easy swapping.
    """

    def __init__(self, target: Target) -> None:
        # We accept Target for interface symmetry; no ssh required.
        self.t = target

    # --------------- lifecycle ---------------
    def close(self) -> None:
        # Nothing to close for local operations.
        return

    # --------------- simple checks ---------------
    def check_available(self) -> Tuple[bool, str]:
        """
        Sanity check that we can run a trivial local command.
        """
        try:
            proc = subprocess.run(
                ["echo", "ok"], capture_output=True, text=True, timeout=5
            )
            if proc.returncode == 0 and proc.stdout.strip() == "ok":
                return True, "Local environment reachable"
            return False, f"Local check failed: rc={proc.returncode}, stderr={proc.stderr.strip()}"
        except Exception as e:
            return False, f"Local command failed: {e}"

    # --------------- exec & file ops ---------------
    def exec(
        self,
        cmd: str,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: int = 300,
    ):
        """
        Execute a shell command locally. Returns (exit_code, stdout, stderr).
        """
        print(f"[DEBUG] Executing local command: {cmd} (cwd={cwd}, env={env})")
        # Merge env with current env for safety
        run_env = os.environ.copy()
        if env:
            # ensure all values are strings
            run_env.update({k: str(v) for k, v in env.items()})

        # Use shell=True to match SSH 'exec_command' semantics.
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or None,
            env=run_env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def put_bytes(self, data: bytes, remote_path: str, mode: int = 0o644) -> None:
        """
        Write bytes to a local file path (creates parent dirs).
        """
        print(f"[DEBUG] Writing {len(data)} bytes to {remote_path} with mode {oct(mode)}")
        parent = os.path.dirname(remote_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(remote_path, "wb") as f:
            f.write(data)
        os.chmod(remote_path, mode)

    def put_file(self, local_path: str, remote_path: str, mode: int = 0o644) -> None:
        """
        Copy a local file to another local path (creates parent dirs).
        """
        print(f"[DEBUG] Copying file {local_path} to {remote_path} with mode {oct(mode)}")
        parent = os.path.dirname(remote_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.copy2(local_path, remote_path)
        os.chmod(remote_path, mode)

    def get_file(self, remote_path: str, local_path: str) -> None:
        """
        "Download" (copy) a local file to a local destination (creates parent dirs).
        """
        print(f"[DEBUG] Copying local file {remote_path} to {local_path}")
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        shutil.copy2(remote_path, local_path)

    def list_files(self, remote_path: str, recursive: bool = False) -> list[str]:
        """
        List files in a local directory. If recursive, traverse subdirectories.
        """
        files: list[str] = []

        def _walk_dir(root: str) -> None:
            for entry in os.scandir(root):
                full = os.path.join(root, entry.name)
                try:
                    st = entry.stat(follow_symlinks=False)
                except FileNotFoundError:
                    # Handle race conditions
                    continue
                if stat.S_ISDIR(st.st_mode):
                    if recursive:
                        _walk_dir(full)
                else:
                    files.append(full)

        print(f"[DEBUG] Listing files in local directory {remote_path} (recursive={recursive})")
        _walk_dir(remote_path)
        return files

    def get(self, remote_path: str, local_path: str) -> None:
        """
        Copy a file or directory (recursively) preserving structure.

        Behaviour:
        - If `remote_path` is a FILE:
            * If `local_path` is an existing directory (or ends with a path separator),
              the file will be saved as `local_path/<basename(remote_path)>`.
            * Otherwise it is treated as the full destination filename.
        - If `remote_path` is a DIRECTORY:
            * Its *basename* will be created under `local_path`, then contents
              mirrored recursively: `local_path/<basename(remote_path)>/**`.
        """
        def _is_dir(path: str) -> bool:
            try:
                return stat.S_ISDIR(os.stat(path, follow_symlinks=False).st_mode)
            except FileNotFoundError:
                return False

        def _copy_dir(src_dir: str, dst_dir: str) -> None:
            for root, dirs, files in os.walk(src_dir):
                rel = os.path.relpath(root, src_dir)
                target_root = os.path.join(dst_dir, rel) if rel != "." else dst_dir
                os.makedirs(target_root, exist_ok=True)
                # Create subdirs
                for d in dirs:
                    os.makedirs(os.path.join(target_root, d), exist_ok=True)
                # Copy files
                for f in files:
                    src_f = os.path.join(root, f)
                    dst_f = os.path.join(target_root, f)
                    print(f"[DEBUG] Copying file {src_f} to {dst_f}")
                    # follow_symlinks=True (default) to copy file content
                    shutil.copy2(src_f, dst_f)

        print(f"[DEBUG] Mirroring from {remote_path} to {local_path}")
        if _is_dir(remote_path):
            base = os.path.basename(remote_path.rstrip(os.sep)) or "root"
            root_local = os.path.join(local_path, base)
            os.makedirs(root_local, exist_ok=True)
            _copy_dir(remote_path, root_local)
        else:
            dest = local_path
            if (os.path.isdir(local_path)) or local_path.endswith((os.sep, "/")):
                dest = os.path.join(local_path, os.path.basename(remote_path))
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            print(f"[DEBUG] Copying file {remote_path} to {dest}")
            shutil.copy2(remote_path, dest)
