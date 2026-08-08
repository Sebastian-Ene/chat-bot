"""E2E tests for the chat page: initial render, and behavior as the
conversation grows.

Locators use accessible roles/names and visible text, never ids or classes,
so tests don't break when markup/styling is refactored.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.locators import chat_heading, conversation_log, message_input, send_button

pytestmark = pytest.mark.e2e

MAX_MESSAGES_TO_SEND = 20


def test_page_loads_with_expected_elements(page: Page, live_server: str) -> None:
    page.goto(live_server + "/")

    expect(page).to_have_title("chat-bot")
    expect(chat_heading(page)).to_be_visible()
    expect(conversation_log(page)).to_be_visible()
    expect(message_input(page)).to_be_visible()
    expect(message_input(page)).to_be_empty()
    expect(send_button(page)).to_be_visible()
    expect(send_button(page)).to_be_enabled()


def _bubble_count(page: Page) -> int:
    return conversation_log(page).evaluate("el => el.childElementCount")


def _is_overflowing(page: Page) -> bool:
    return conversation_log(page).evaluate("el => el.scrollHeight > el.clientHeight")


def _send_message_and_wait_for_reply(page: Page, text: str) -> None:
    """Send a message and wait for both the user bubble and the reply bubble
    to appear, regardless of what the reply says."""
    before = _bubble_count(page)
    message_input(page).fill(text)
    send_button(page).click()
    expect(page.get_by_text(text, exact=True)).to_be_visible()
    page.wait_for_function(
        "expected => document.querySelector('[role=log]').childElementCount >= expected",
        arg=before + 2,
    )


def test_title_and_input_stay_visible_with_long_conversation(page: Page, live_server: str) -> None:
    page.goto(live_server + "/")
    page.set_viewport_size({"width": 800, "height": 600})

    sent = 0
    while not _is_overflowing(page):
        sent += 1
        assert sent <= MAX_MESSAGES_TO_SEND, "sent many messages without ever overflowing the conversation log"
        _send_message_and_wait_for_reply(page, f"test message {sent}")

    # one more turn on top of the now-overflowing log
    _send_message_and_wait_for_reply(page, "one more message after overflow")

    assert _is_overflowing(page), "expected the conversation log to still be overflowing"

    body_overflow = page.evaluate("document.body.scrollHeight > window.innerHeight + 1")
    assert not body_overflow, "page itself grew taller than the viewport — .chat is no longer height-capped"

    expect(chat_heading(page)).to_be_in_viewport()
    expect(message_input(page)).to_be_in_viewport()
    expect(send_button(page)).to_be_in_viewport()


def test_conversation_log_scrolls_to_reveal_latest_reply(page: Page, live_server: str) -> None:
    page.goto(live_server + "/")
    page.set_viewport_size({"width": 800, "height": 600})

    sent = 0
    while not _is_overflowing(page):
        sent += 1
        assert sent <= MAX_MESSAGES_TO_SEND, "sent many messages without ever overflowing the conversation log"
        _send_message_and_wait_for_reply(page, f"scroll test message {sent}")

    scrolled_to_bottom = conversation_log(page).evaluate(
        "el => el.scrollTop + el.clientHeight >= el.scrollHeight - 1"
    )
    assert scrolled_to_bottom, "conversation log did not scroll to reveal the latest reply"
