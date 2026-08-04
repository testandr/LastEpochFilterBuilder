from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    """Abstract base parser. All concrete parsers should inherit from this class.

    Parsers should not perform I/O in __init__.
    """

    def __init__(self, *, http_client: Any = None, cache: Any = None, config: Any = None) -> None:
        self.http_client = http_client
        self.cache = cache
        self.config = config

    @abstractmethod
    def parse(self, source: str) -> Any:
        """Parse the given source (URL or raw content) and return structured DTO.

        source: URL or raw HTML depending on implementation.
        """
        raise NotImplementedError
