"""Table Row element module."""

from ..base.ui_element import UIElement
from ..decorators import retry_if_stale_element_error


class TableRowElement(UIElement):
    """Class for TextElement element model."""

    @retry_if_stale_element_error
    def get_row_values(self) -> list[str]:
        """Get Element value."""
        row_cells = self.find_elements()

        return [cell.text for cell in row_cells]
