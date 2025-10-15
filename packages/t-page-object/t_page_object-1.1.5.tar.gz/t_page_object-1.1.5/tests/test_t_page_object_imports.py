#!/usr/bin/env python
"""Tests for `t_page_object` package."""
import unittest


class TestTPageObject(unittest.TestCase):
    """Smoke tests of the package."""

    def test_creation_of_elements(self):
        """Test that all elements can be initialised."""
        try:
            from t_page_object.elements.button_element import ButtonElement  # noqa
            from t_page_object.elements.checkbox_element import CheckboxElement  # noqa
            from t_page_object.elements.checkox_element import CheckboxElement  # noqa
            from t_page_object.elements.container_element import ContainerElement  # noqa
            from t_page_object.elements.dropdown_element import DropdownElement  # noqa
            from t_page_object.elements.iframe_element import IFrameElement  # noqa
            from t_page_object.elements.image_element import ImageElement  # noqa
            from t_page_object.elements.input_element import InputElement  # noqa
            from t_page_object.elements.table_element import TableElement  # noqa
            from t_page_object.elements.text_element import TextElement  # noqa
            from t_page_object.elements.sentinel_element import SentinelElement  # noqa

            assert True
        except Exception as e:
            print(f"Couldn't initialise all elements with error: {e}")
            assert False

    def test_base_classes(self):
        """Test that all base classes can be initialised."""
        try:
            from t_page_object.base.base_app import BaseApp  # noqa
            from t_page_object.base.base_page import BasePage  # noqa
            from t_page_object.base.endpoint_element import EndpointElement  # noqa
            from t_page_object.base.ui_element import UIElement  # noqa

            assert True
        except Exception as e:
            print(f"Couldn't initialise all base classes with error: {e}")
            assert False

    def test_bot_config(self):
        """Test that bot config can be initialised and variables be configured correctly."""
        from t_page_object.bot_config import BotConfig

        test_value = "test_value"
        BotConfig.configure(output_folder=test_value)
        from t_page_object.bot_config import BotConfig

        assert BotConfig.output_folder == test_value


if __name__ == "__main__":
    unittest.main()
