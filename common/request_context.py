"""Per-request correlation id.

Carried in a `ContextVar` rather than threaded through every function signature,
so any module can log without taking an id parameter. A logging filter copies it
onto each record, and the formatter prints it — so one request's whole trace is
`grep <id> logs/app.log`.
"""
import logging
from contextvars import ContextVar
from uuid import uuid4

UNSET = "-"

_request_id: ContextVar[str] = ContextVar("request_id", default=UNSET)


def new_request_id() -> str:
    """Short enough to eyeball, long enough not to collide in a PoC."""
    return uuid4().hex[:8]


def set_request_id(request_id: str) -> None:
    _request_id.set(request_id)


def get_request_id() -> str:
    return _request_id.get()


class RequestIdFilter(logging.Filter):
    """Attached to the loggers (not the handlers) so every record carries the id,
    including records captured by pytest's `caplog`."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
