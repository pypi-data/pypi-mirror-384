"""Dropdown element module."""

from typing import Literal
from ..base.ui_element import UIElement
from ..decorators import retry_if_stale_element_error


class DropdownElement(UIElement):
    """Standard dropdown element."""

    def __init__(self, *args, option_tag: str = "li", **kwargs):
        """Initialise dropdown element."""
        super().__init__(*args, **kwargs)
        self.option_tag = option_tag

    @retry_if_stale_element_error
    def type_and_enter(self, *text_to_enter) -> None:
        """Selects an option from the dropdown list based on the provided text.

        The text is input into the dropdown list input and the Enter key is pressed to select the option.

        Args:
            text_to_enter (str): The text/s of the option to be selected from the dropdown list.
            option_tag (str): The tag used for the different options. Defaults to 'li'.

        Returns:
            None
        """
        text_to_enter = tuple(text_to_enter)
        for text in text_to_enter:
            self.input_text(text)
            self.press_key(r"\13")

    @retry_if_stale_element_error
    def click_and_select_option(
        self, text_to_find: str, match_strategy: Literal["exact", "contains"] = "exact"
    ) -> bool:
        """Selects an option from the dropdown list based on the provided text.

        The dropdown list is clicked to open the list and the option is selected.

        Args:
            text_to_find (str): The text of the option to be selected from the dropdown list.
            match_strategy (Literal["exact", "contains"], optional): The strategy for matching the text.
                "exact" for exact match (default), "contains" for partial match. Defaults to "exact".

        Returns:
            bool: Is the requested option present in the list.
        """
        self.click_element_when_visible()

        if match_strategy == "exact":
            xpath = f"""{self.xpath}//{self.option_tag}[
                translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') =
                '{text_to_find.lower()}'
            ]"""
        elif match_strategy == "contains":
            xpath = f"""{self.xpath}//{self.option_tag}[
                contains(
                    translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),
                    '{text_to_find.lower()}'
                )
            ]"""
        else:
            raise ValueError(f"Invalid match_strategy: {match_strategy}. Must be 'exact' or 'contains'.")

        if self.browser.find_elements(xpath):
            self.browser.get_webelement(xpath).click()
            return True
        return False

    @retry_if_stale_element_error
    def get_selected_option(self, by="value") -> str:
        """Gets the selected option."""
        if by == "text":
            value = self.find_element().text
        else:
            value = self.find_element().get_attribute(by)
        return value
