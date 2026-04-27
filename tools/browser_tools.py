"""Browser interaction tools for GenericAgent.

Provides tools for navigating and interacting with web pages via TMWebDriver.
"""

from __future__ import annotations

import time
from typing import Optional

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from TMWebDriver import Session
from tools.base_tool import BaseTool, register_tool


@register_tool
class NavigateTool(BaseTool):
    """Navigate the browser to a given URL."""

    name = "navigate"
    description = "Navigate the browser to the specified URL."
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The fully-qualified URL to navigate to (e.g. https://example.com).",
            }
        },
        "required": ["url"],
    }

    def run(self, url: str, session: Session) -> str:  # type: ignore[override]
        driver = session.driver
        driver.get(url)
        return f"Navigated to {url}. Page title: {driver.title!r}"


@register_tool
class ClickTool(BaseTool):
    """Click an element identified by a CSS selector."""

    name = "click"
    description = "Click the first element matching the given CSS selector."
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector for the element to click.",
            },
            "timeout": {
                "type": "number",
                "description": "Seconds to wait for the element to be clickable (default 10).",
            },
        },
        "required": ["selector"],
    }

    def run(self, selector: str, session: Session, timeout: float = 10.0) -> str:  # type: ignore[override]
        driver = session.driver
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return f"Clicked element matching selector {selector!r}."
        except TimeoutException:
            return f"Timeout: no clickable element found for selector {selector!r} within {timeout}s."
        except ElementNotInteractableException:
            return f"Element matching {selector!r} is not interactable."


@register_tool
class TypeTextTool(BaseTool):
    """Type text into an input element."""

    name = "type_text"
    description = "Clear an input field and type the given text into it, then optionally press Enter."
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector for the input element.",
            },
            "text": {
                "type": "string",
                "description": "Text to type into the element.",
            },
            "press_enter": {
                "type": "boolean",
                "description": "Whether to press Enter after typing (default false).",
            },
        },
        "required": ["selector", "text"],
    }

    def run(  # type: ignore[override]
        self,
        selector: str,
        text: str,
        session: Session,
        press_enter: bool = False,
    ) -> str:
        driver = session.driver
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            element.clear()
            element.send_keys(text)
            if press_enter:
                element.send_keys(Keys.RETURN)
            return f"Typed {text!r} into {selector!r}" + (" and pressed Enter." if press_enter else ".")
        except (TimeoutException, NoSuchElementException):
            return f"Element not found for selector {selector!r}."


@register_tool
class GetPageTextTool(BaseTool):
    """Return the visible text content of the current page."""

    name = "get_page_text"
    description = "Return the visible text content of the currently loaded page (truncated to 4000 chars)."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def run(self, session: Session) -> str:  # type: ignore[override]
        driver = session.driver
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            text = body.text.strip()
            if len(text) > 4000:
                text = text[:4000] + "\n...[truncated]"
            return text or "(Page body is empty)"
        except NoSuchElementException:
            return "Could not find page body element."
