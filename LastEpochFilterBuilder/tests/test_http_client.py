import pytest
import requests

from app.utils.http_client import HttpClient, HttpResponse
from app.utils.cache_manager import CacheManager
from app.utils.retry import RetryPolicy


class DummyResp:
    def __init__(self, text="ok", status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP %d" % self.status_code)


def test_httpclient_success(monkeypatch, tmp_path):
    # mock requests.Session.get
    def fake_get(self, url, headers, timeout):
        return DummyResp(text="<html>ok</html>", status_code=200)

    monkeypatch.setattr("requests.Session.get", fake_get)

    cache = CacheManager(base_path=tmp_path, ttl_seconds=10)
    client = HttpClient(timeout=5, user_agent="UA", cache=cache, retry_policy=RetryPolicy(attempts=1))
    resp = client.get("http://example.com", cache_subdir="tier_lists")
    assert isinstance(resp, HttpResponse)
    assert "ok" in resp.text
    # cached
    assert cache.exists("tier_lists", "http://example.com")


def test_httpclient_connection_error(monkeypatch, tmp_path):
    def fake_get(self, url, headers, timeout):
        raise requests.exceptions.ConnectionError("conn error")

    monkeypatch.setattr("requests.Session.get", fake_get)
    client = HttpClient(timeout=1, user_agent="UA", cache=None, retry_policy=RetryPolicy(attempts=1))
    with pytest.raises(Exception):
        client.get("http://nope.example")


def test_httpclient_timeout_and_retries(monkeypatch, tmp_path):
    calls = {"n": 0}

    def fake_get(self, url, headers, timeout):
        calls["n"] += 1
        raise requests.exceptions.Timeout("timeout")

    monkeypatch.setattr("requests.Session.get", fake_get)

    rp = RetryPolicy(attempts=3, delay_seconds=0.01, backoff_factor=2.0)
    client = HttpClient(timeout=1, user_agent="UA", cache=None, retry_policy=rp, sleep_callable=lambda s: None)
    with pytest.raises(Exception):
        client.get("http://timeout.example")
    assert calls["n"] == 3


def test_httpclient_uses_cache_when_fresh(monkeypatch, tmp_path):
    # Ensure that when cache is fresh, requests.get is not called
    called = {"get": False}

    def fake_get(self, url, headers, timeout):
        called["get"] = True
        return DummyResp("not used")

    monkeypatch.setattr("requests.Session.get", fake_get)
    cache = CacheManager(base_path=tmp_path, ttl_seconds=60)
    cache.save("tier_lists", "http://example.com/fresh", "cached content")

    client = HttpClient(timeout=5, user_agent="UA", cache=cache, retry_policy=RetryPolicy(attempts=1))
    resp = client.get("http://example.com/fresh", cache_subdir="tier_lists")
    assert not called["get"]
    assert "cached content" in resp.text
