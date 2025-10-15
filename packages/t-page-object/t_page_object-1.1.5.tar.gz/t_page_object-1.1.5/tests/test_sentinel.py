"""
Test module for SentinelElement class.

This module contains tests for the SentinelElement functionality
which is a simple wrapper around UIElement for basic UI operations.
"""

from unittest.mock import Mock
from t_page_object.elements.sentinel_element import SentinelElement


class TestSentinelElement:
    """
    Test suite for SentinelElement class.

    Tests:
    - test_initialization: Tests proper initialization with xpath and browser
    - test_inheritance: Tests that SentinelElement properly inherits from UIElement
    - test_basic_functionality: Tests basic UIElement functionality through SentinelElement
    - test_xpath_access: Tests that xpath property is accessible
    - test_browser_access: Tests that browser property is accessible
    - test_repr_method: Tests the __repr__ method inherited from UIElement
    """

    def test_initialization(self):
        """Test proper initialization with xpath and browser."""
        # set
        mock_browser = Mock()
        xpath = "//input[@id='username']"

        # execute
        sentinel_element = SentinelElement(xpath, mock_browser)

        # assert
        assert sentinel_element.xpath == xpath
        assert sentinel_element.browser == mock_browser
        assert isinstance(sentinel_element, SentinelElement)

    def test_inheritance(self):
        """Test that SentinelElement properly inherits from UIElement."""
        # set
        mock_browser = Mock()
        xpath = "//input[@id='username']"

        # execute
        sentinel_element = SentinelElement(xpath, mock_browser)

        # assert
        from t_page_object.base.ui_element import UIElement

        assert isinstance(sentinel_element, UIElement)
        assert hasattr(sentinel_element, "wait_element_load")
        assert hasattr(sentinel_element, "format_xpath")
        assert hasattr(sentinel_element, "wait_element_unavailable")

    def test_basic_functionality(self):
        """Test basic UIElement functionality through SentinelElement."""
        # set
        mock_browser = Mock()
        xpath = "//button[@id='submit']"
        sentinel_element = SentinelElement(xpath, mock_browser)

        # execute
        sentinel_element.format_xpath()

        # assert
        assert sentinel_element.xpath == xpath
        assert sentinel_element.original_xpath == xpath

    def test_xpath_access(self):
        """Test that xpath property is accessible."""
        # set
        mock_browser = Mock()
        xpath = "//div[@class='container']"
        sentinel_element = SentinelElement(xpath, mock_browser)

        # execute & assert
        assert sentinel_element.xpath == xpath
        assert sentinel_element.original_xpath == xpath

    def test_browser_access(self):
        """Test that browser property is accessible."""
        # set
        mock_browser = Mock()
        xpath = "//span[@id='text']"
        sentinel_element = SentinelElement(xpath, mock_browser)

        # execute & assert
        assert sentinel_element.browser == mock_browser

    def test_repr_method(self):
        """Test the __repr__ method inherited from UIElement."""
        # set
        mock_browser = Mock()
        xpath = "//input[@type='text']"
        sentinel_element = SentinelElement(xpath, mock_browser)

        # execute
        repr_string = repr(sentinel_element)

        # assert
        assert repr_string == "<UIElement>"

    def test_default_parameters(self):
        """Test initialization with default parameters."""
        # set
        mock_browser = Mock()
        xpath = "//a[@href='test']"

        # execute
        sentinel_element = SentinelElement(xpath, mock_browser)

        # assert
        assert sentinel_element.wait is True
        assert sentinel_element.id == ""
        assert sentinel_element.timeout is None
        assert sentinel_element.name_in_page is None
        assert sentinel_element.page_name is None

    def test_custom_parameters(self):
        """Test initialization with custom parameters."""
        # set
        mock_browser = Mock()
        xpath = "//input[@name='custom']"

        # execute
        sentinel_element = SentinelElement(xpath, mock_browser)

        # assert
        assert sentinel_element.xpath == xpath
        assert sentinel_element.browser == mock_browser
        assert sentinel_element.original_xpath == xpath

    def test_dynamic_xpath_formatting(self):
        """Test dynamic xpath formatting functionality."""
        # set
        mock_browser = Mock()
        dynamic_xpath = "//input[@id='{}']"
        sentinel_element = SentinelElement(dynamic_xpath, mock_browser)

        # execute
        sentinel_element.format_xpath("username")

        # assert
        assert sentinel_element.xpath == "//input[@id='username']"
        assert sentinel_element.original_xpath == dynamic_xpath

    def test_multiple_instances(self):
        """Test that multiple SentinelElement instances work independently."""
        # set
        mock_browser = Mock()
        xpath1 = "//input[@id='first']"
        xpath2 = "//input[@id='second']"

        # execute
        sentinel1 = SentinelElement(xpath1, mock_browser)
        sentinel2 = SentinelElement(xpath2, mock_browser)

        # assert
        assert sentinel1.xpath == xpath1
        assert sentinel2.xpath == xpath2
        assert sentinel1.xpath != sentinel2.xpath
        assert sentinel1.browser == sentinel2.browser
