import os
from pathlib import Path

import pytest

from app.config.config_manager import ConfigManager


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_defaults(tmp_path):
    cm = ConfigManager(base_path=tmp_path)
    cfg = cm.load()
    assert cfg.filter.max_rules == 140
    assert isinstance(cfg.maxroll.urls, list)
    assert cfg.cache.path == "data/cache"


def test_yaml_overrides_defaults(tmp_path):
    yaml_path = tmp_path / "config.yaml"
    write_file(yaml_path, """
maxroll:
  request_delay: 5
cache:
  path: custom/cache
filter:
  max_rules: 100
""")
    cm = ConfigManager(base_path=tmp_path)
    cfg = cm.load()
    assert cfg.maxroll.request_delay == 5
    assert cfg.cache.path == "custom/cache"
    assert cfg.filter.max_rules == 100


def test_env_overrides_yaml(tmp_path, monkeypatch):
    yaml_path = tmp_path / "config.yaml"
    write_file(yaml_path, """
maxroll:
  timeout: 10
  urls:
    - https://example.com/a
""")
    env_path = tmp_path / ".env"
    write_file(env_path, "MAXROLL_TIMEOUT=55\nCACHE_PATH=env/cache\nFILTER_MAX_RULES=77\n")

    cm = ConfigManager(base_path=tmp_path)
    cfg = cm.load()
    assert cfg.maxroll.timeout == 55
    assert cfg.cache.path == "env/cache"
    assert cfg.filter.max_rules == 77


def test_missing_required_raises(tmp_path):
    # write yaml that removes urls
    write_file(tmp_path / "config.yaml", "maxroll: { urls: [] }\n")
    cm = ConfigManager(base_path=tmp_path)
    with pytest.raises(ValueError):
        cm.load()
