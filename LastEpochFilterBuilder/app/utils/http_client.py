from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from .cache_manager import CacheManager
from .retry import RetryPolicy


logger = logging.getLogger("app.utils.http_client")


@dataclass
class HttpResponse:
    status_code: int
    text: str
    headers: Dict[str, Any]


class HttpClient:
    def __init__(
        self,
        timeout: float = 20.0,
        user_agent: Optional[str] = None,
        cache: Optional[CacheManager] = None,
        retry_policy: Optional[RetryPolicy] = None,
        sleep_callable: Optional[callable] = None,
    ) -> None:
        self.timeout = timeout
        self.user_agent = user_agent or "LastEpochFilterBot/1.0"
        self.session = requests.Session()
        self.cache = cache
        self.retry_policy = retry_policy or RetryPolicy()
        self.sleep = sleep_callable or time.sleep

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def get(
        self,
        url: str,
        cache_subdir: Optional[str] = None,
        use_cache: bool = True,
    ) -> HttpResponse:
        logger.info("GET %s", url)

        # Try cache first
        if use_cache and self.cache and cache_subdir:
            try:
                if self.cache.exists(cache_subdir, url) and self.cache.is_fresh(cache_subdir, url):
                    logger.info("Cache hit for %s", url)
                    text = self.cache.load(cache_subdir, url)
                    return HttpResponse(status_code=200, text=text or "", headers={})
            except Exception:
                logger.exception("Cache error for %s", url)

        last_exc = None
        attempts = max(1, self.retry_policy.attempts)
        for attempt in range(1, attempts + 1):
            try:
                resp = self.session.get(url, headers=self._headers(), timeout=self.timeout)
                resp.raise_for_status()
                text = resp.text
                # Save to cache
                if use_cache and self.cache and cache_subdir:
                    try:
                        self.cache.save(cache_subdir, url, text)
                    except Exception:
                        logger.exception("Failed to save cache for %s", url)
                return HttpResponse(status_code=resp.status_code, text=text, headers=dict(resp.headers))
            except requests.exceptions.RequestException as e:
                last_exc = e
                logger.warning("Request failed (%s) attempt %d/%d for %s", e, attempt, attempts, url)
                if attempt < attempts:
                    delay = self.retry_policy.get_delay(attempt)
                    logger.info("Retrying after %.2f seconds", delay)
                    try:
                        self.sleep(delay)
                    except Exception:
                        pass
                continue

        # All attempts failed
        logger.error("All attempts failed for %s: %s", url, last_exc)
        raise last_exc
