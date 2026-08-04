import time
from pathlib import Path

from app.utils.cache_manager import CacheManager


def test_cache_save_and_load(tmp_path):
    cm = CacheManager(base_path=tmp_path, ttl_seconds=10)
    key = "http://example.com/page"
    sub = "tier_lists"
    content = "<html>ok</html>"
    p = cm.save(sub, key, content)
    assert p.exists()
    loaded = cm.load(sub, key)
    assert loaded == content


def test_cache_ttl(tmp_path):
    cm = CacheManager(base_path=tmp_path, ttl_seconds=1)
    key = "http://example.com/page2"
    sub = "builds"
    cm.save(sub, key, "data")
    assert cm.exists(sub, key)
    assert cm.is_fresh(sub, key)
    # wait
    time.sleep(1.2)
    assert not cm.is_fresh(sub, key)


def test_cache_clear(tmp_path):
    cm = CacheManager(base_path=tmp_path, ttl_seconds=10)
    cm.save("items", "k1", "a")
    cm.save("items", "k2", "b")
    assert cm.exists("items", "k1")
    cm.clear()
    # directory emptied
    assert not (tmp_path / "items").exists()
