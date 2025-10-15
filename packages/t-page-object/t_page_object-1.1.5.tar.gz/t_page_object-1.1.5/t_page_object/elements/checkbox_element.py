"""Checkbox element module."""

from ..base.ui_element import UIElement
from ..decorators import retry_if_stale_element_error


class CheckboxElement(UIElement):
    """Checkbox element."""

    @retry_if_stale_element_error
    def select(self) -> None:
        """Selects the checkbox element."""
        self.click_element_when_visible()
