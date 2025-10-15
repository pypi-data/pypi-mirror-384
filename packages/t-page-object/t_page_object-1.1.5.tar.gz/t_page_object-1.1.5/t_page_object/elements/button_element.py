"""Button element module."""

from RPA.Browser.Selenium import Selenium

from .. import logger
from ..base.ui_element import UIElement
from ..bot_config import BotConfig
from ..decorators import retry_if_stale_element_error


class ButtonElement(UIElement):
    """Standard button element."""

    def __init__(
        self,
        xpath: str,
        browser: Selenium,
        dev_safe_sensitive: bool = False,
        wait: bool = True,
        id: str = "",
        timeout: int = 10,
    ):
        """
        Initializes a button element with specified parameters.

        Args:
            xpath (str): The XPath expression used to locate the button element.
            dev_safe_sensitive (bool, optional): Indicates whether the button is
            sensitive to development-safe operations. Defaults to False.
            wait (bool, optional): Whether to wait for the button element to be present. Defaults to True.

        Returns:
            None
        """
        super().__init__(xpath=xpath, browser=browser, wait=wait, id=id, timeout=timeout)
        self.dev_safe_sensitive = dev_safe_sensitive

    @retry_if_stale_element_error
    def click(self) -> None:
        """Main click method for button element.

        Checks if button is dev_save_sensitive and if dev_safe_mode is enabled.
        """
        button_description = f"Button {self.name_in_page}" if self.name_in_page else "Button"
        if self.dev_safe_sensitive and BotConfig.dev_safe_mode:
            logger.debug(
                f"{button_description} not clicked: The element is dev safe sensitive, and DEV_SAFE_MODE is enabled"
            )
        else:
            super().__getattr__("click_element_if_visible")()
            logger.debug(
                f"{button_description} clicked: "
                f"dev_safe_sensitive={self.dev_safe_sensitive}, "
                f"dev_safe_mode={BotConfig.dev_safe_mode}"
            )

    def click_button(self) -> None:
        """Redirects to click method."""
        self.click()

    def click_button_when_visible(self) -> None:
        """Redirects to click method."""
        self.click()

    def click_button_if_visible(self) -> None:
        """Redirects to click method."""
        self.click()

    def click_element(self) -> None:
        """Redirects to click method."""
        self.click()

    def click_element_if_visible(self) -> None:
        """Redirects to click method."""
        self.click()

    def click_element_when_visible(self) -> None:
        """Redirects to click method."""
        self.click()

    def click_element_when_clickable(self) -> None:
        """Redirects to click method."""
        self.click()

    @retry_if_stale_element_error
    def javascript_click(self) -> None:
        """Click element using JavaScript."""
        self.browser.driver.execute_script("arguments[0].click()", self.browser.find_element(self.xpath))
