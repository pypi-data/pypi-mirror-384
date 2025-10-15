"""Contains the UIElement class."""
import base64
import io
from contextlib import suppress

from .. import logger
from ..bot_config import BotConfig
from retry import retry
from selenium.common import (  # type: ignore
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from RPA.Browser.Selenium import Selenium  # type: ignore
from ..bug_catcher_meta import BugCatcherMeta
from typing import Callable, TypeVar, Optional, Any
from time import sleep, monotonic
from PIL import Image
import re


T = TypeVar("T", bound="UIElement")


class UIElement(metaclass=BugCatcherMeta):
    """This is an UI Element used to build each Page."""

    def __init__(
        self,
        xpath: str,
        browser: Selenium,
        wait: bool = True,
        id: str = "",
        timeout: Optional[int] = None,
    ) -> None:
        """
        Initializes a base element with specified parameters.

        Args:
            xpath (str): The XPath expression used to locate the element,
                could also be a formattable string for dynamic XPaths.
            wait (bool, optional): Wait for the element to be present. Defaults to True.
            id (str, optional): An optional identifier for the element. Defaults to None.
            timeout (int, optional): The maximum time to wait for the element to be present, in seconds.

        """
        self.xpath = xpath
        self.wait = wait
        self.id = id
        self.timeout = timeout
        self.original_xpath = xpath
        self.browser: Selenium = browser

        self.name_in_page = None
        self.page_name = None

    def __repr__(self) -> str:
        """Return a string representation of the UIElement instance.

        The default repr slows down the debugging process too much.
        So, this was made to avoid that and help developers debug their agents faster.
        """
        return "<UIElement>"

    def __set_name__(self, owner, name):
        """Called when the attribute is set in the class.

        Args:
            owner: The class where this descriptor is defined.
            name: The name of the attribute.
        """
        self.name_in_page = name
        self.page_name = owner.__name__

    @retry(
        exceptions=(
            StaleElementReferenceException,
            ElementClickInterceptedException,
            NoSuchElementException,
            ElementNotInteractableException,
            AssertionError,
            TimeoutException,
        ),
        tries=2,
        delay=1,
    )
    def format_xpath(self, *args: list, **kwargs: dict) -> None:
        """If using a dynamic xpath, this method formats the xpath string.

        Args:
            *args (list): The arguments to be used to format the xpath.
            **kwargs (dict): The keyword arguments to be used to format the
        """
        self.xpath = self.original_xpath.format(*args, **kwargs)

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """Delegate method calls not found in this class to the Selenium instance."""
        if not self.browser.get_browser_ids():
            return None  # type: ignore

        if BotConfig.handle_alerts:
            self._handle_alert()
        if not self.wait_element_load():
            logger.debug(f"Element not found: {self.xpath}. Wait is set to False. Doing nothing")
            return lambda *args, **kwargs: None
        return lambda *args, **kwargs: self._selenium_method(name, *args, **kwargs)

    def _selenium_method(self, name: str, *args, **kwargs) -> Callable:
        """Executing self.browser.name(*args,**kwargs) method.

        For example: self.browser.click_element(self.xpath)
        """
        method = getattr(self.browser, name, None)

        if not method:
            raise AttributeError(f"Method '{name}' not found in Selenium instance.")

        try:
            return method(self.xpath, *args, **kwargs)
        except ElementClickInterceptedException as e:
            if not BotConfig.close_modals:
                raise e

            logger.debug("Element click intercepted. Attempting to close modal window...")

            self._close_modal(str(e))

            try:
                return method(self.xpath, *args, **kwargs)
            except ElementClickInterceptedException as ex:
                logger.debug("Element click intercepted. Attempting to remove covering element...")
                self._remove_covering_element(str(ex))
                return method(self.xpath, *args, **kwargs)

    @retry(
        exceptions=(
            StaleElementReferenceException,
            ElementClickInterceptedException,
            NoSuchElementException,
            ElementNotInteractableException,
            AssertionError,
            TimeoutException,
        ),
        tries=2,
        delay=1,
    )
    def wait_element_load(
        self,
        timeout: Optional[int] = None,
        verify_is_displayed: bool = True,
        raise_error: bool = True,
    ) -> bool:
        """
        Wait for an element to load.

        Args:
            timeout (int, optional): The maximum time to wait for the element to be present, in seconds.
                Defaults to None. Overwrites apps inherent timeout if set.
            verify_is_displayed (bool): If True, besides validating if the element is present inside the DOM, it will
                also verify if it is displayed. Defaults to True.
            raise_error (bool): If True, raise an AssertionError if the element is not found or not visible
                within the timeout. If False, return False instead of raising an error. Defaults to True.
        Returns:
            bool: True if the element is found and passes the visibility check (if enabled).
                  False if not found or not displayed within the timeout and raise_error is False.

        Raises:
            AssertionError: If the element is not found or not displayed within the timeout and raise_error is True.
        """
        timeout = timeout or self.timeout or BotConfig.default_timeout
        deadline = monotonic() + timeout

        while monotonic() < deadline:
            with suppress(Exception):
                element = self.browser.find_element(self.xpath)
                if not verify_is_displayed or element.is_displayed():
                    return True
            sleep(0.5)

        if self.wait:
            if raise_error:
                raise AssertionError(f"Element '{self.xpath}' not visible.")
            return False
        return False

    def wait_element_unavailable(self, timeout: Optional[int] = None) -> bool:
        """Wait for an element to disappear from the DOM.

        Args:
            timeout (int, optional): The maximum time to wait for the element to disappear in seconds.
                Defaults to None. Overwrites apps inherent timeout if set.

        Returns:
            bool: True if the element is unavailable, False otherwise.
        """
        timeout = timeout or self.timeout or BotConfig.default_timeout
        deadline = monotonic() + timeout

        while monotonic() < deadline:
            if not self.browser.does_page_contain_element(self.xpath):
                return True
            sleep(1)
        return False

    def _handle_alert(self):
        """Handle alert if present."""
        try:
            self.browser.alert_should_not_be_present(BotConfig.alert_handling_option)
        except AssertionError:
            logger.debug(f"Alert detected. Handling with option: {BotConfig.alert_handling_option}")

    def _get_element_from_message(self, exception_message: str) -> tuple[str, str, str]:
        """Get element from exception message.

        Args:
            exception_message (str): The exception message.
        """
        is_firefox = self.browser.driver.capabilities.get("browserName", "") == "firefox"

        if is_firefox:
            return self._get_element_from_message_firefox(exception_message)

        return self._get_element_from_message_chrome(exception_message)

    def _get_element_from_message_chrome(self, exception_message: str) -> tuple[str, str, str]:
        """Get element from exception message for Chrome."""
        match = re.search(r"Other element would receive the click: <(.+?)>", exception_message)
        if match:
            blocking_element_html = match.group(1)
            logger.debug(f"Blocking element: {blocking_element_html}")
            tag_match = re.match(r"(\w+)", blocking_element_html)
            tag = tag_match.group(1) if tag_match else ""

            id_match = re.search(r'id="([^"]+)"', blocking_element_html)
            if id_match:
                locator = "id"
                locator_value = id_match.group(1)
            else:
                attr_matches = re.findall(r'(\w+)="([^"]+)"', blocking_element_html)
                for attr_name, attr_value in attr_matches:
                    if attr_name != "style":
                        locator = attr_name
                        locator_value = attr_value
                        break
                else:
                    locator = ""
                    locator_value = ""
            return tag, locator, locator_value
        return "", "", ""

    def _get_element_from_message_firefox(self, exception_message: str) -> tuple[str, str, str]:
        """Get element from exception message for Firefox."""
        match = re.search(r"because another element <(.+?)>", exception_message)
        if match:
            blocking_element_html = match.group(1)
            logger.debug(f"Blocking element: {blocking_element_html}")
            tag_match = re.match(r"(\w+)", blocking_element_html)
            tag = tag_match.group(1) if tag_match else ""

            id_match = re.search(r'id="([^"]+)"', blocking_element_html)
            if id_match:
                locator = "id"
                locator_value = id_match.group(1)
            else:
                attr_matches = re.findall(r'(\w+)="([^"]+)"', blocking_element_html)
                for attr_name, attr_value in attr_matches:
                    if attr_name != "style":
                        locator = attr_name
                        locator_value = attr_value
                        break
                else:
                    locator = ""
                    locator_value = ""
            return tag, locator, locator_value
        return "", "", ""

    def _close_modal(self, exception_message: str) -> None:
        """Attempt to accept or close modal."""
        tag, locator, locator_value = self._get_element_from_message(exception_message)

        if not all((tag, locator, locator_value)):
            return

        common_close_button_paths_and_indexes: list[tuple[str, int]] = []

        if BotConfig.modal_button:
            common_close_button_paths_and_indexes.append((f"//button[text()='{BotConfig.modal_button}']", 0))

        common_close_button_paths_and_indexes.extend(
            [
                ("//button[text()='Close']", 0),
                ("//button", -1),
                ("//input", -1),
            ]
        )

        base_xpath = f"//{tag}[@{locator}='{locator_value}']"

        for xpath, index in common_close_button_paths_and_indexes:
            elements = self.browser.find_elements(base_xpath + xpath)
            if not elements:
                continue

            logger.debug(f"Clicking on the blocking element: {elements[index].get_attribute('outerHTML')}")
            elements[index].click()

            try:
                self.browser.wait_until_element_is_not_visible(base_xpath + xpath)
                break
            except AssertionError:
                logger.debug(f"Element still visible after trying to close modal: {base_xpath + xpath}")
                continue

    def _remove_covering_element(self, exception_message: str) -> None:
        """Remove covering element."""
        tag, locator, locator_value = self._get_element_from_message(exception_message)
        js_script = f"""document.querySelector('{tag}[{locator}="{locator_value}"]').style.display = 'none';"""
        self.browser.execute_javascript(js_script)

    @retry(
        exceptions=(
            StaleElementReferenceException,
            NoSuchElementException,
            ElementNotInteractableException,
            AssertionError,
            TimeoutException,
        ),
        tries=2,
        delay=1,
    )
    def get_element_attribute(self, attribute: str) -> Any:
        """Encapsulates the 'self.browser.get_element_attribute' method.

        Args:
            attribute (str): Element desired attribute name.
        """
        return self.browser.get_element_attribute(self.xpath, attribute)

    def does_page_contain_element(self, count: int | None = None) -> bool:
        """Encapsulates the 'self.browser.does_page_contain_element' method.

        Args:
            count (int): How many times the element is expected to appear on page
                by default one or more.
        """
        return self.browser.does_page_contain_element(self.xpath, count)

    def is_element_visible(self, timeout: Optional[int] = None) -> bool:
        """Encapsulates the 'self.browser.is_element_visible' method.

        Args:
            timeout (int, optional): The maximum time to wait for the element to be visible, in seconds.
                Defaults to None. Overwrites apps inherent timeout if set.
        """
        return self.browser.is_element_visible(self.xpath, timeout)

    def scroll_to_element(self, center: bool = True) -> None:
        """Scroll to the element on the page instantly.

        Args:
            center: Whether to center the element in the viewport
        """
        element = self.browser.find_element(self.xpath)
        behavior = "auto"  # always instant scroll
        block = "center" if center else "start"
        script = f"arguments[0].scrollIntoView({{behavior: '{behavior}', block: '{block}'}});"
        self.browser.driver.execute_script(script, element)

    def take_element_screenshot(self, file_path: str, crop: bool = True) -> None:
        """Take a screenshot of the element and save it to a file.

        Args:
            file_path (str): Full file path to save the screenshot.
            crop (bool, optional): Whether to crop the screenshot before taking the screenshot.
        """
        # Scroll element into center view
        self.scroll_to_element()

        # Takes full page screenshot and processes it
        screenshot_base64 = self.browser.driver.get_screenshot_as_base64()
        screenshot_data = base64.b64decode(screenshot_base64)
        image = Image.open(io.BytesIO(screenshot_data))

        if crop:
            element = self.browser.find_element(self.xpath)

            # Calculates exact element coordinates considering scroll position
            scroll_y = self.browser.driver.execute_script("return window.pageYOffset")
            location = element.location
            size = element.size

            # Crops to exact element dimensions
            left = location["x"]
            top = location["y"] - scroll_y
            right = left + size["width"]
            bottom = top + size["height"]

            # Crops the and saved the image to the exact element dimensions
            image = image.crop((left, top, right, bottom))

        image.save(file_path)
