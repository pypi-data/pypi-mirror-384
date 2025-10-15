"""Sentinel element."""

from RPA.Browser.Selenium import Selenium
from t_page_object.base.ui_element import UIElement


class SentinelElement(UIElement):
    """Sentinel element. This element is a generic element to represent an ui element to basic operations.

    The idea is to avoid using UIElement directly when It is necessary for a generic element to represent
    an ui element to basic operations.
    """

    def __init__(self, xpath: str, browser: Selenium):
        """Initialize the sentinel element."""
        super().__init__(xpath, browser)
