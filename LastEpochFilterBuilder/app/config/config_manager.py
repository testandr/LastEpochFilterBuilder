from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class ApplicationConfig:
    name: str = "Last Epoch Smart Loot Filter"


@dataclass
class MaxrollConfig:
    urls: List[str]
    request_delay: int = 1
    timeout: int = 20


@dataclass
class CacheConfig:
    enabled: bool = True
    path: str = "data/cache"
    ttl_seconds: int = 86400


@dataclass
class DatabaseConfig:
    type: str = "sqlite"
    path: str = "data/database.sqlite"


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: Optional[str] = None


@dataclass
class FilterConfig:
    max_rules: int = 140


@dataclass
class Config:
    application: ApplicationConfig
    maxroll: MaxrollConfig
    cache: CacheConfig
    database: DatabaseConfig
    logging: LoggingConfig
    filter: FilterConfig


class ConfigManager:
    """Loads configuration from defaults, optional config.yaml and .env files.

    Priority (highest → lowest): .env > config.yaml > defaults
    """

    DEFAULTS: Dict[str, Any] = {
        "application": {"name": "Last Epoch Smart Loot Filter"},
        "maxroll": {
            "urls": [
                "https://maxroll.gg/last-epoch/tierlists/corruption-tier-list",
                "https://maxroll.gg/last-epoch/tierlists/speed-farming-tier-list",
                "https://maxroll.gg/last-epoch/tierlists/bossing-tier-list",
            ],
            "request_delay": 1,
            "timeout": 20,
        },
        "cache": {"enabled": True, "path": "data/cache", "ttl_seconds": 86400},
        "database": {"type": "sqlite", "path": "data/database.sqlite"},
        "logging": {"level": "INFO", "file": None},
        "filter": {"max_rules": 140},
    }

    ENV_MAP: Dict[str, str] = {
        # env var name -> dotted config path
        "MAXROLL_URLS": "maxroll.urls",
        "MAXROLL_TIMEOUT": "maxroll.timeout",
        "MAXROLL_REQUEST_DELAY": "maxroll.request_delay",
        "CACHE_ENABLED": "cache.enabled",
        "CACHE_PATH": "cache.path",
        "CACHE_TTL_SECONDS": "cache.ttl_seconds",
        "DATABASE_TYPE": "database.type",
        "DATABASE_PATH": "database.path",
        "LOGGING_LEVEL": "logging.level",
        "LOGGING_FILE": "logging.file",
        "FILTER_MAX_RULES": "filter.max_rules",
    }

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = Path(base_path or Path.cwd())
        self.config_path = self.base_path / "config.yaml"
        self.env_path = self.base_path / ".env"
        self._raw: Dict[str, Any] = {}
        self.config: Optional[Config] = None

    def load(self) -> Config:
        # Start with defaults
        cfg = dict(self.DEFAULTS)

        # Load YAML if exists
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                try:
                    y = yaml.safe_load(f) or {}
                except Exception:
                    y = {}
            self._deep_update(cfg, y)

        # Load .env (highest priority)
        if self.env_path.exists():
            load_dotenv(self.env_path)

        # Apply environment overrides
        self._apply_env_overrides(cfg)

        # Normalize and construct dataclasses
        self._raw = cfg
        self.config = Config(
            application=ApplicationConfig(**cfg.get("application", {})),
            maxroll=MaxrollConfig(**cfg.get("maxroll", {})),
            cache=CacheConfig(**cfg.get("cache", {})),
            database=DatabaseConfig(**cfg.get("database", {})),
            logging=LoggingConfig(**cfg.get("logging", {})),
            filter=FilterConfig(**cfg.get("filter", {})),
        )

        # Validate required fields
        self._validate()

        return self.config

    def _deep_update(self, dest: Dict[str, Any], src: Dict[str, Any]) -> None:
        for k, v in src.items():
            if (
                k in dest
                and isinstance(dest[k], dict)
                and isinstance(v, dict)
            ):
                self._deep_update(dest[k], v)
            else:
                dest[k] = v

    def _apply_env_overrides(self, cfg: Dict[str, Any]) -> None:
        for env_name, path in self.ENV_MAP.items():
            if env_name in os.environ:
                raw = os.environ[env_name]
                self._set_by_path(cfg, path, self._coerce_value(raw, path))

    def _set_by_path(self, cfg: Dict[str, Any], path: str, value: Any) -> None:
        parts = path.split(".")
        node = cfg
        for p in parts[:-1]:
            if p not in node or not isinstance(node[p], dict):
                node[p] = {}
            node = node[p]
        node[parts[-1]] = value

    def _coerce_value(self, raw: str, path: str) -> Any:
        # Simple coercion rules based on path
        key = path.split(".")[-1]
        if key in ("enabled",):
            return raw.lower() in ("1", "true", "yes", "on")
        if key in ("timeout", "request_delay", "ttl_seconds", "max_rules"):
            try:
                return int(raw)
            except ValueError:
                return raw
        if key == "urls":
            # comma separated
            return [u.strip() for u in raw.split(",") if u.strip()]
        return raw

    def _validate(self) -> None:
        # Required: maxroll.urls non-empty, database.path non-empty
        if not self.config:
            raise RuntimeError("Config not loaded")

        if not self.config.maxroll.urls or not isinstance(self.config.maxroll.urls, list):
            raise ValueError("maxroll.urls must be a non-empty list in configuration")

        if not self.config.database.path:
            raise ValueError("database.path must be set in configuration")

        if not isinstance(self.config.filter.max_rules, int) or self.config.filter.max_rules <= 0:
            raise ValueError("filter.max_rules must be a positive integer")
