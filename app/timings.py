"""Per-stage latency measurement (requirements.md §7.2).

Timings are a DEBUG-level concern: when the performance logger is above DEBUG,
`create_timings()` hands back a no-op that makes no `perf_counter()` calls at
all — the measurement is genuinely off, not taken and thrown away.

Stage names are free-form, so the stages still to be built (rewrite, embed,
search, expansion) need no change here.
"""
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter

from app.logging_config import PERFORMANCE_LOGGER


class NoOpTimings:
    """Same interface as `RequestTimings`, measuring nothing."""

    enabled = False

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        yield

    def mark_first_token(self) -> None:
        pass

    def log(self, **fields: object) -> None:
        pass


class RequestTimings:
    """Collects stage durations, time-to-first-token and total, in milliseconds."""

    enabled = True

    def __init__(self) -> None:
        self._started = perf_counter()
        self.stages: dict[str, float] = {}
        self.time_to_first_token: float | None = None

    @staticmethod
    def _ms(seconds: float) -> float:
        return round(seconds * 1000, 2)

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        started = perf_counter()
        try:
            yield
        finally:
            self.stages[name] = self._ms(perf_counter() - started)

    def mark_first_token(self) -> None:
        """First call wins — later chunks are not the first token."""
        if self.time_to_first_token is None:
            self.time_to_first_token = self._ms(perf_counter() - self._started)

    @property
    def total(self) -> float:
        return self._ms(perf_counter() - self._started)

    def log(self, **fields: object) -> None:
        parts = [f"{key}={value}" for key, value in fields.items()]
        parts.append(f"ttft_ms={self.time_to_first_token}")
        parts.append(f"total_ms={self.total}")
        parts.extend(f"{name}_ms={duration}" for name, duration in self.stages.items())
        logging.getLogger(PERFORMANCE_LOGGER).debug(" ".join(parts))


def create_timings() -> RequestTimings | NoOpTimings:
    if logging.getLogger(PERFORMANCE_LOGGER).isEnabledFor(logging.DEBUG):
        return RequestTimings()
    return NoOpTimings()
