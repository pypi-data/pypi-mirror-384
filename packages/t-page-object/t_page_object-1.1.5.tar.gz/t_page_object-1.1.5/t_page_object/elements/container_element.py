"""Class for container elements."""

from typing import Type, TypeVar

from t_object import ThoughtfulObject  # type: ignore

from ..base.ui_element import UIElement
from ..decorators import retry_if_stale_element_error

TO = TypeVar("TO", bound=ThoughtfulObject)


class ContainerElement:
    """Container element. Used to hold multiple text elements."""

    def __init__(self, *args: UIElement) -> None:
        """Initializes a container element with list of text elements.

        Args:
            *args (list[TextElement]): List of text elements

        """
        self.elements: tuple[UIElement, ...] = args

    @retry_if_stale_element_error
    def get_text_values(self, cls: Type[TO]) -> Type[TO]:
        """Get text for each element with id matching class attribute.

        Args:
            cls (Type[TO]): The class to use for the object.

        Returns:
            Instance of input class with text values.
        """
        kwargs = {}
        for k, _ in cls.__annotations__.items():
            for element in self.elements:
                if element.id == k:
                    text = element.get_text()
                    kwargs[k] = "" if not text else text
        return cls(**kwargs)

    @retry_if_stale_element_error
    def set_text_values(self, cls: Type[TO]) -> None:
        """Sets text for each element with id matching class attribute.

        Args:
            cls (Type[TO]): The object to use for the text values.
        """
        for k, _ in cls.__annotations__.items():
            for element in self.elements:
                if element.id == k:
                    element.click_and_input_text(cls.__dict__[k])

    @retry_if_stale_element_error
    def check_if_all_elements_contain_value(self) -> bool:
        """Get text for each attribute in object with matching id."""
        all_filled = all(element.get_element_attribute("value") for element in self.elements)
        return all_filled
