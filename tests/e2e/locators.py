"""Shared accessible-role/name locators for the chat page.

Kept in one place so every e2e test targets the same accessible
roles/names instead of re-deriving (or drifting from) them, and so
none of them reach for ids or CSS classes. See .claude/skills/e2e-testing.
"""
from playwright.sync_api import Locator, Page


def chat_heading(page: Page) -> Locator:
    return page.get_by_role("heading", name="chat-bot", level=1)


def message_input(page: Page) -> Locator:
    return page.get_by_role("textbox", name="Chat message")


def send_button(page: Page) -> Locator:
    return page.get_by_role("button", name="Send")


def conversation_log(page: Page) -> Locator:
    return page.get_by_role("log", name="Conversation")