"""Contains the BasePage class which is the parent class for all page objects in the project."""

import copy
import datetime
from pathlib import Path
from selenium.webdriver.remote.webelement import WebElement
from SeleniumLibrary.errors import ElementNotFound  # type: ignore
from RPA.Browser.Selenium import Selenium  # type: ignore
from .ui_element import UIElement
from typing import Optional
from PIL import Image
from abc import ABC
from ..exceptions import NoVerificationElement, NoURL


class BasePage(ABC):
    """Base page class for all page objects in the project."""

    browser: Selenium = Selenium
    url: str = ""
    verification_element: Optional[UIElement] = None

    def __init__(self, browser: Selenium):
        """Base Page."""
        # Get the Selenium instance based on the portal name (if provided)
        self.browser = browser

    def __deepcopy__(self):
        """Custom deepcopy to avoid copying the Selenium browser instance."""
        new_copy = copy.copy(self)  # Perform shallow copy
        new_copy.browser = self.browser  # Prevent deep copying the Selenium instance
        return new_copy

    def visit(self, raise_error: bool = True) -> None:
        """Navigate to the base page URL.

        raise_error (bool): If True, raise an AssertionError if the element is not found or not visible
                within the timeout. If False, return False instead of raising an error. Defaults to True.
        """
        if not self.url:
            raise NoURL("URL not set for page.")
        if self.url != self.browser.driver.current_url:
            self.browser.go_to(self.url)
        self.wait_page_load(raise_error=raise_error)

    def wait_page_load(self, timeout=None, raise_error: bool = True) -> None:
        """Wait for the page to load by waiting for the verification element to load.

        timeout: The maximum time to wait for the element to be present, in seconds.
        raise_error (bool): If True, raise an AssertionError if the element is not found or not visible
            within the timeout. If False, return False instead of raising an error. Defaults to True.
        """
        if self.verification_element:
            self.verification_element.wait_element_load(timeout=timeout, raise_error=raise_error)
        else:
            raise NoVerificationElement("Verification element not set for page.")

    def is_in_page(self, timeout: Optional[int] = None) -> bool:
        """Check if It is in the page."""
        try:
            self.wait_page_load(timeout)
            return True
        except AssertionError:
            return False

    def wait_for_new_window_and_switch(self, old_window_handles: list, raise_error: bool = True) -> Optional[bool]:
        """Function for waiting and switching to new window.

            Args:
                old_window_handles: The list of window handles before the new window is opened.
                raise_error (bool): If True, raise an AssertionError if the element is not found or not visible
                    within the timeout. If False, return False instead of raising an error. Defaults to True.

        `   Returns:
                Optional[bool]: Result of switch_window() if a new window is found;
                            False if no new window appears and raise_error is False;
                            otherwise, raises TimeoutError.
        """
        timeout = datetime.datetime.now() + datetime.timedelta(seconds=30)
        while datetime.datetime.now() < timeout:
            currents_window_handles = self.browser.get_window_handles()
            if len(currents_window_handles) > len(old_window_handles):
                window = [window for window in currents_window_handles if window not in old_window_handles][0]
                return self.browser.switch_window(window)
        else:
            if raise_error:
                raise TimeoutError("New window was not opened")
            return False

    def get_element_from_shadow_roots(self, *roots, element_css: str) -> WebElement:
        """Get element from nested shadow roots.

        Args:
            roots: The css locators of the shadow root elements, in hierarchal order.
            element_css: The css locator of the element to find.

        Returns:
            The WebElement of the element found.
        """
        javascript_code = (
            "return document"
            + "".join([f".querySelector('{x}').shadowRoot" for x in roots])
            + f".querySelector('{element_css}')"
        )
        element = self.browser.execute_javascript(javascript_code)
        if not isinstance(element, WebElement):
            raise ElementNotFound(f"Element not found in shadow root: {element_css}")
        return element

    def screenshot(self, locator: Optional[str] = None, filename: str = "", convert_to_webp: bool = False) -> str:
        """Capture page or element screenshot.

        Args:
            locator (str | None, optional): Locator for capture element screenshot. Defaults to None.
            filename (str | None, optional): filename to be used for screenshot image. Defaults to "".
            convert_to_webp (bool, optional): Defines if image should be converted to webp or not. Defaults to False.

        Returns:
            str: Path to screenshot image.
        """
        screenshot_filename = self.browser.screenshot(locator, str(filename))

        if screenshot_filename and convert_to_webp:
            path_screenshot_filename: Path = Path(screenshot_filename)
            with Image.open(path_screenshot_filename) as image:
                converted_filename = path_screenshot_filename.with_suffix(".webp")
                image.save(converted_filename, "WEBP")

            return str(converted_filename)

        return str(screenshot_filename)

    def scroll_to_top(self) -> None:
        """Scroll to the top of the page instantly."""
        behavior = "auto"  # always instant scroll
        script = f"window.scrollTo({{top: 0, behavior: '{behavior}'}});"
        self.browser.driver.execute_script(script)
