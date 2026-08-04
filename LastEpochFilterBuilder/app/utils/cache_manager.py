from __future__ import annotations

import os
import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import time


@dataclass
class CacheManager:
    base_path: Path
    ttl_seconds: int = 86400

    def __post_init__(self):
        self.base_path = Path(self.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path_for(self, subdir: str, key: str) -> Path:
        safe = hashlib.sha1(key.encode("utf-8")).hexdigest()
        path = self.base_path / subdir
        path.mkdir(parents=True, exist_ok=True)
        return path / f"{safe}.html"

    def save(self, subdir: str, key: str, content: str) -> Path:
        p = self._path_for(subdir, key)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return p

    def load(self, subdir: str, key: str) -> Optional[str]:
        p = self._path_for(subdir, key)
        if not p.exists():
            return None
        with open(p, "r", encoding="utf-8") as f:
            return f.read()

    def exists(self, subdir: str, key: str) -> bool:
        return self._path_for(subdir, key).exists()

    def is_fresh(self, subdir: str, key: str) -> bool:
        p = self._path_for(subdir, key)
        if not p.exists():
            return False
        mtime = p.stat().st_mtime
        return (time.time() - mtime) <= self.ttl_seconds

    def clear(self) -> None:
        # remove everything under base_path
        if self.base_path.exists():
            for child in self.base_path.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
