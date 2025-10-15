from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
import yaml
from filelock import FileLock
from deployman.models import AppConfig, Target


DEFAULT_PATH = Path(os.environ.get("DEPLOYMAN_CONFIG", "~/.deployman/config.yaml")).expanduser()
LOCK_PATH = DEFAULT_PATH.with_suffix(".lock")


class ConfigRepository:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(LOCK_PATH))

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        with self.lock:
            with self.path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        return AppConfig.model_validate(data)

    def save(self, cfg: AppConfig) -> None:
        with self.lock:
            with self.path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(cfg.model_dump(mode="python"), f, sort_keys=False)

    # convenience helpers
    def add_target(self, t: Target) -> None:
        cfg = self.load()
        cfg.ensure_unique(t)
        cfg.targets[t.name] = t
        self.save(cfg)

    def remove_target(self, name: str) -> bool:
        cfg = self.load()
        existed = name in cfg.targets
        if existed:
            del cfg.targets[name]
            self.save(cfg)
        return existed