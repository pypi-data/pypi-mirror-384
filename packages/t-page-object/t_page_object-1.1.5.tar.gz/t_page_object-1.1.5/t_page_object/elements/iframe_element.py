"""Frame element module."""

from ..base.ui_element import UIElement
from ..decorators import retry_if_stale_element_error


class IFrameElement(UIElement):
    """Class for frame element model."""

    @retry_if_stale_element_error
    def select_iframe(self) -> None:
        """Select frame."""
        self.select_frame()

    @retry_if_stale_element_error
    def unselect_iframe(self) -> None:
        """Selects base frame."""
        self.browser.unselect_frame()

    def select_nested_iframe(self, *frames: list, from_base=False) -> None:
        """Select nested frame.

        Args:
            frames: list of frame locators
            from_base: bool, if True, unselects the current frame before selecting the nested frames
        """
        if from_base:
            self.browser.unselect_frame()
        for frame in frames:
            self.select_frame(frame)
