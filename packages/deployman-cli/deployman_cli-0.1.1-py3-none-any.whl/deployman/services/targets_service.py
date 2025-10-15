from __future__ import annotations
from typing import Iterable, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from deployman.models import Target, SSHSettings
from deployman.storage import ConfigRepository
from deployman.connectors import ConnectorFactory


class TargetsService:
    def __init__(self, repo: ConfigRepository | None = None) -> None:
        self.repo = repo or ConfigRepository()

    def list(self) -> List[Target]:
        cfg = self.repo.load()
        return list(cfg.targets.values())

    def load_target(self, name: str) -> Optional[Target]:
        cfg = self.repo.load()
        return cfg.targets.get(name)

    def add(self, *, name: str, tags: Iterable[str], host: str, port: int, username: str | None, key_path: str | None) -> Target:
        t = Target(
            name=name,
            connector="ssh",
            tags=set(filter(None, (tag.strip() for tag in tags))),
            ssh=SSHSettings(host=host, port=port, username=username, key_path=key_path),
        )
        self.repo.add_target(t)
        return t

    def remove(self, name: str) -> bool:
        return self.repo.remove_target(name)

    def check(self, names: Optional[List[str]] = None, max_workers: int = 8) -> List[Tuple[str, bool, str]]:
        """Return a list of (name, ok, message) for the selected targets (or all if names is None)."""
        cfg = self.repo.load()
        targets = list(cfg.targets.keys())
        selected = targets if names is None else [n for n in targets if n in targets]
        results: List[Tuple[str, bool, str]] = []
        if not selected:
            return results

        def _run(n: str) -> Tuple[str, bool, str]:
            if n not in cfg.targets:
                return (n, False, "Target not found")
            c = ConnectorFactory.create(cfg.targets[n])
            ok, msg = c.check_available()
            return (n, ok, msg)

        workers = min(max_workers, max(1, len(selected)))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            future_map = {ex.submit(_run, n): n for n in selected}
            for fut in as_completed(future_map):
                results.append(fut.result())
        # stable order by name
        results.sort(key=lambda x: x[0])
        return results
