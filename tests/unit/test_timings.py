import logging

import pytest

from api.core.timings import NoOpTimings, RequestTimings, TokenUsage, create_timings
from common.logging_config import PERFORMANCE_LOGGER


@pytest.fixture
def performance_logger() -> logging.Logger:
    """Always change the level via `setLevel` — assigning `.level` directly
    leaves `isEnabledFor`'s cache stale."""
    logger = logging.getLogger(PERFORMANCE_LOGGER)
    original = logger.level
    yield logger
    logger.setLevel(original)


def test_stage_records_a_duration() -> None:
    timings = RequestTimings()

    with timings.stage("retrieval"):
        pass

    assert "retrieval" in timings.stages
    assert timings.stages["retrieval"] >= 0


def test_stage_records_duration_even_when_the_body_raises() -> None:
    timings = RequestTimings()

    with pytest.raises(RuntimeError), timings.stage("generation"):
        raise RuntimeError("boom")

    assert "generation" in timings.stages


def test_first_token_is_not_overwritten_by_later_chunks() -> None:
    timings = RequestTimings()

    timings.mark_first_token()
    first = timings.time_to_first_token
    timings.mark_first_token()

    assert timings.time_to_first_token == first


def test_time_to_first_token_is_not_greater_than_total() -> None:
    timings = RequestTimings()
    timings.mark_first_token()

    assert timings.time_to_first_token <= timings.total


def test_log_emits_stages_ttft_and_total(
    performance_logger: logging.Logger, caplog: pytest.LogCaptureFixture
) -> None:
    timings = RequestTimings()
    with timings.stage("retrieval"):
        pass
    timings.mark_first_token()

    with caplog.at_level(logging.DEBUG, logger=PERFORMANCE_LOGGER):
        timings.log(message_length=11)

    message = caplog.text
    assert "retrieval_ms=" in message
    assert "ttft_ms=" in message
    assert "total_ms=" in message
    assert "message_length=11" in message


def test_token_usage_reads_the_sdk_counters() -> None:
    from types import SimpleNamespace

    usage = TokenUsage.from_sdk(SimpleNamespace(input_tokens=120, output_tokens=30))

    assert usage.input_tokens == 120
    assert usage.output_tokens == 30


def test_token_usage_tolerates_missing_counters() -> None:
    """Not every response carries every field — cost data must not crash a reply."""
    usage = TokenUsage.from_sdk(None)

    assert usage.input_tokens == 0
    assert usage.cache_read_input_tokens == 0


def test_usage_totals_across_stages() -> None:
    timings = RequestTimings()

    timings.usage_recorder("analysis")(TokenUsage(input_tokens=100, output_tokens=20))
    timings.usage_recorder("generation")(TokenUsage(input_tokens=400, output_tokens=90))

    assert sum(u.input_tokens for u in timings.usage.values()) == 500
    assert sum(u.output_tokens for u in timings.usage.values()) == 110


def test_noop_timings_asks_callers_not_to_fetch_usage() -> None:
    """No performance logging means no reason to pay for `get_final_message`."""
    assert NoOpTimings().usage_recorder("generation") is None


def test_create_timings_measures_when_performance_logging_is_debug(
    performance_logger: logging.Logger,
) -> None:
    performance_logger.setLevel(logging.DEBUG)

    assert isinstance(create_timings(), RequestTimings)


def test_create_timings_is_a_noop_above_debug(
    performance_logger: logging.Logger,
) -> None:
    performance_logger.setLevel(logging.INFO)

    timings = create_timings()

    assert isinstance(timings, NoOpTimings)
    assert not timings.enabled


def test_noop_timings_records_nothing() -> None:
    timings = NoOpTimings()

    with timings.stage("retrieval"):
        pass
    timings.mark_first_token()
    timings.log(message_length=11)

    assert not hasattr(timings, "stages")
