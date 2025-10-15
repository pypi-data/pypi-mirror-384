"""Unit tests for the retry_if_stale_element_error decorator applied to the ButtonElement.click method."""

from unittest.mock import MagicMock, patch

import pytest
from selenium.common import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
)

from t_page_object.decorators import MAX_RETRIES
from t_page_object.elements.button_element import ButtonElement
from t_page_object.selenium_manager import SeleniumManager


@pytest.fixture(autouse=True)
def mock_time_sleep():
    """Fixture that automatically patches `time.sleep` to prevent real sleep delays during testing."""
    with patch("time.sleep", return_value=None):
        yield


@pytest.fixture(autouse=True)
def mock_ui_element_get_attr():
    """Fixture that mocks the `__getattr__` method of the UIElement class and the SeleniumManager class."""
    with (patch("t_page_object.base.ui_element.UIElement.__getattr__") as mock_getattr,):
        yield mock_getattr


class TestRetryIfStaleElementError:
    """Test class for verifying the retry behavior of the `click` method in the ButtonElement class."""

    def setup_method(self) -> None:
        """Sets up the button element to be used in every test."""
        self.browser = SeleniumManager.get_instance("test_app")
        self.button_element = ButtonElement(xpath="//button", browser=self.browser)

    def test_click_succeeds_first_try(self, mock_ui_element_get_attr: MagicMock):
        """Tests `click` method succeeds on the first try without retrying."""
        # Mocking the 'click_element_if_visible' method to do nothing
        mock_ui_element_get_attr.return_value = lambda: None

        self.button_element.click()

        mock_ui_element_get_attr.assert_called_once_with("click_element_if_visible")

    @pytest.mark.parametrize(
        "exception",
        [
            StaleElementReferenceException(),
            ElementClickInterceptedException(),
            NoSuchElementException(),
        ],
    )
    def test_click_retries_on_exceptions(self, mock_ui_element_get_attr: MagicMock, exception: Exception):
        """Tests `click` method retries the operation when certain exceptions are raised."""
        # Mocking the 'click_element_if_visible' method to raise an exception first, then succeed
        mock_ui_element_get_attr.side_effect = [exception, lambda: None]

        self.button_element.click()

        # Asserting that the 'click_element_if_visible' method was called twice (retrying once)
        assert mock_ui_element_get_attr.call_count == 2

    def test_click_fails_after_max_retries(self, mock_ui_element_get_attr: MagicMock):
        """Tests `click` method raises an exception after the maximum number of retries is reached."""
        # Mocking the 'click_element_if_visible' method to always raise a StaleElementReferenceException
        mock_ui_element_get_attr.side_effect = StaleElementReferenceException()

        # Verifying that the StaleElementReferenceException is raised after 5 retries
        with pytest.raises(StaleElementReferenceException):
            self.button_element.click()

        # Asserting that the 'click_element_if_visible' method was called 5 times (max retries)
        assert mock_ui_element_get_attr.call_count == MAX_RETRIES
