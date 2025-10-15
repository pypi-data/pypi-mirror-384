"""This module contains the TextElement class for the text element model."""

from ..base.ui_element import UIElement
from ..decorators import retry_if_stale_element_error


class TextElement(UIElement):
    """Input element."""

    @retry_if_stale_element_error
    def get_clean_text(self):
        """Get text from element and clean."""
        text = self.get_text().strip().lower()
        return text
