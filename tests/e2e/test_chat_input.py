"""E2E tests for the message input as it grows.

The input is a textarea so a long question stays readable while it is being
written. Two behaviours here can break silently and are only observable in a
real browser: the box growing with its content, and Enter still sending once
the element is one that natively treats Enter as a newline.

Locators use accessible roles/names, never ids or classes.
"""
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.locators import conversation_log, message_input

pytestmark = pytest.mark.e2e

LONG_MESSAGE = (
    "I have a question about the warranty terms for business customers who "
    "bought the Aurora Home starter kit last spring and now want to return "
    "an opened but complete order, including what restocking fee applies."
)


def input_height(page: Page) -> float:
    return message_input(page).evaluate("el => el.getBoundingClientRect().height")


def bubble_count(page: Page) -> int:
    return conversation_log(page).evaluate("el => el.childElementCount")


class TestGrowing:
    def test_grows_when_the_message_wraps(self, page: Page, live_server: str) -> None:
        page.goto(live_server + "/")
        before = input_height(page)

        message_input(page).fill(LONG_MESSAGE)

        assert input_height(page) > before

    def test_stops_growing_at_the_cap(self, page: Page, live_server: str) -> None:
        """A pasted wall of text must scroll inside the box rather than squeeze
        the conversation off screen."""
        page.goto(live_server + "/")

        message_input(page).fill(LONG_MESSAGE * 10)
        capped = input_height(page)
        message_input(page).fill(LONG_MESSAGE * 40)

        assert input_height(page) == capped

    def test_shrinks_back_after_sending(self, page: Page, live_server: str) -> None:
        """Clearing the value does not shrink a textarea on its own."""
        page.goto(live_server + "/")
        empty = input_height(page)

        message_input(page).fill(LONG_MESSAGE)
        message_input(page).press("Enter")
        expect(message_input(page)).to_be_empty()

        assert input_height(page) == empty


class TestKeyboard:
    def test_enter_sends_the_message(self, page: Page, live_server: str) -> None:
        """A textarea sends Enter to a newline by default; a chat box that needs
        the mouse to send would be a regression."""
        page.goto(live_server + "/")

        message_input(page).fill("does enter still send?")
        message_input(page).press("Enter")

        expect(page.get_by_text("does enter still send?", exact=True)).to_be_visible()
        expect(message_input(page)).to_be_empty()

    def test_shift_enter_writes_a_newline(self, page: Page, live_server: str) -> None:
        page.goto(live_server + "/")
        message_input(page).fill("first line")

        message_input(page).press("Shift+Enter")
        message_input(page).type("second line")

        expect(message_input(page)).to_have_value("first line\nsecond line")
        assert bubble_count(page) == 0, "Shift+Enter must not send"
