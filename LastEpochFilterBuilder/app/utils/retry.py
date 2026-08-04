from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class RetryPolicy:
    attempts: int = 3
    delay_seconds: float = 1.0
    backoff_factor: float = 2.0

    def get_delay(self, attempt: int) -> float:
        """Return delay for given attempt (1-based)."""
        if attempt <= 1:
            return 0.0
        return self.delay_seconds * (self.backoff_factor ** (attempt - 1))

