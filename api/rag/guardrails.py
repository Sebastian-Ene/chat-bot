"""Prompt guardrails on user input (requirements.md §6.3).

Scope is **user input only** — the current question and every history turn,
including the ones attributed to the assistant, since history is client-supplied
and forgeable (§6.4). Indexed documents are trusted for this PoC.

Two layers, deliberately different in kind:

- `sanitize()` is deterministic and always applied. It strips the structural
  power of our own markers so caller text cannot close a block and pose as
  prompt structure.
- `detect_injection()` is a heuristic. It only ever logs: the patterns match
  plenty of legitimate questions ("ignore the first document, what does the
  second say?"), and blocking a real user to catch a string match is the wrong
  trade. Actual mitigation comes from the system prompt and from sanitising.
"""
import logging
import re

from api.core.constants import RESERVED_TAGS
from common.logging_config import APP_LOGGER

logger = logging.getLogger(APP_LOGGER)

_RESERVED_TAG_PATTERN = re.compile(
    r"<\s*/?\s*(?:" + "|".join(RESERVED_TAGS) + r")\b[^>]*>", re.IGNORECASE
)

_INJECTION_PATTERNS = {
    "ignore_instructions": re.compile(
        r"\b(ignore|disregard|forget)\b[^.\n]{0,40}\b(previous|prior|above|earlier|all)\b"
        r"[^.\n]{0,25}\b(instruction|rule|prompt|direction)",
        re.IGNORECASE,
    ),
    "role_override": re.compile(
        r"\b(you are now|from now on,? you|act as|pretend to be|behave as)\b", re.IGNORECASE
    ),
    "prompt_disclosure": re.compile(
        r"\b(reveal|show|print|repeat|output)\b[^.\n]{0,30}"
        r"\b(system prompt|your instructions|these rules)\b",
        re.IGNORECASE,
    ),
    "jailbreak": re.compile(r"\b(developer mode|jailbreak)\b", re.IGNORECASE),
    "injected_directive": re.compile(r"^\s*(new instructions?|system)\s*:", re.IGNORECASE | re.MULTILINE),
}


def sanitize(text: str) -> str:
    """Neutralise our structural markers so caller text cannot break out."""
    return _RESERVED_TAG_PATTERN.sub(
        lambda match: match.group(0).replace("<", "&lt;").replace(">", "&gt;"), text
    )


def detect_injection(text: str) -> list[str]:
    """Names of the injection patterns matching `text`, for logging only."""
    return sorted(name for name, pattern in _INJECTION_PATTERNS.items() if pattern.search(text))


def guard(text: str, *, source: str) -> str:
    """Log anything suspicious, then return text safe to embed in the prompt."""
    matches = detect_injection(text)
    if matches:
        # The text itself is not logged here — the pattern names are what is
        # actionable, and this line is a WARNING that ships at any log level.
        logger.warning(
            "possible prompt injection source=%s patterns=%s", source, ",".join(matches)
        )

    sanitized = sanitize(text)
    if matches or sanitized != text:
        # Only when something actually happened — a line per turn would drown
        # the trace on a long conversation.
        logger.debug(
            "stage=guard source=%s sanitised=%s patterns=%s",
            source,
            sanitized != text,
            ",".join(matches) or "none",
        )
    return sanitized
