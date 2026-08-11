"""Per-stage latency measurement (requirements.md §7.2).

Timings are a DEBUG-level concern: when the performance logger is above DEBUG,
`create_timings()` hands back a no-op that makes no `perf_counter()` calls at
all — the measurement is genuinely off, not taken and thrown away.

Stage names are free-form, so the stages still to be built (rewrite, embed,
search, expansion) need no change here.
"""
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter

from app.logging_config import PERFORMANCE_LOGGER


@dataclass(frozen=True)
class TokenUsage:
    """Token counts from one API call — the raw material for cost analysis."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

    @classmethod
    def from_sdk(cls, usage: object) -> "TokenUsage":
        """Tolerant of missing fields: not every response carries every counter."""
        return cls(
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            cache_read_input_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_input_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        )


class NoOpTimings:
    """Same interface as `RequestTimings`, measuring nothing."""

    enabled = False

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        yield

    def mark_first_token(self) -> None:
        pass

    def record_usage(self, stage: str, usage: TokenUsage) -> None:
        pass

    def usage_recorder(self, stage: str) -> Callable[[TokenUsage], None] | None:
        """`None` tells the caller not to bother fetching usage at all."""
        return None

    def log(self, **fields: object) -> None:
        pass


class RequestTimings:
    """Collects stage durations, time-to-first-token and total, in milliseconds."""

    enabled = True

    def __init__(self) -> None:
        self._started = perf_counter()
        self.stages: dict[str, float] = {}
        self.usage: dict[str, TokenUsage] = {}
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

    def record_usage(self, stage: str, usage: TokenUsage) -> None:
        self.usage[stage] = usage

    def usage_recorder(self, stage: str) -> Callable[[TokenUsage], None]:
        def record(usage: TokenUsage) -> None:
            self.record_usage(stage, usage)

        return record

    def log(self, **fields: object) -> None:
        parts = [f"{key}={value}" for key, value in fields.items()]
        parts.append(f"ttft_ms={self.time_to_first_token}")
        parts.append(f"total_ms={self.total}")
        parts.extend(f"{name}_ms={duration}" for name, duration in self.stages.items())

        # Totals first — they are what cost is computed from — then per stage, so
        # it is visible which call is doing the spending.
        parts.append(f"tokens_in={sum(u.input_tokens for u in self.usage.values())}")
        parts.append(f"tokens_out={sum(u.output_tokens for u in self.usage.values())}")
        parts.append(
            f"cache_read={sum(u.cache_read_input_tokens for u in self.usage.values())}"
        )
        for name, usage in self.usage.items():
            parts.append(f"{name}_tokens_in={usage.input_tokens}")
            parts.append(f"{name}_tokens_out={usage.output_tokens}")

        logging.getLogger(PERFORMANCE_LOGGER).debug(" ".join(parts))


def create_timings() -> RequestTimings | NoOpTimings:
    if logging.getLogger(PERFORMANCE_LOGGER).isEnabledFor(logging.DEBUG):
        return RequestTimings()
    return NoOpTimings()
