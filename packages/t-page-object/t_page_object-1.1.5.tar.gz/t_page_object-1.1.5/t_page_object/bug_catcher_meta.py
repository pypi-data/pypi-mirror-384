"""Classes for bug catcher."""

import os

from . import logger
from .bot_config import BotConfig
from t_bug_catcher import attach_file_to_exception, report_error  # type: ignore
from typing import Callable, Any
import re
import inspect
import functools


def _get_lineno(stack: list[inspect.FrameInfo]):
    """Get the line number of the calling module.

    Args:
        stack (list): The stack of the calling module.

    Returns:
        int: The line number of the calling module.
    """
    for frame_info in stack[1:]:
        if (
            "element" in frame_info.filename
            or "base" in frame_info.filename
            or "bug_catcher_meta" in frame_info.filename
        ):
            continue
        file = frame_info.filename.split("/")[-1].replace(".py", "")
        lineno = frame_info.lineno
        return file, lineno
    return None, None


def _clean_filename(filename: str, extension: str = "png") -> str:
    filename = re.sub(r"[^a-zA-Z0-9]", "_", filename)
    return f"{filename}.{extension}"


def _attach_browser_data_if_error(func: Callable) -> Callable:
    """Decorator to attach browser data to exception if error occurs.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The decorated function.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Callable:
        if args:
            self = args[0]
            if isinstance(self.__class__, BugCatcherMeta):
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    if hasattr(self, "browser") and BotConfig.capture_screenshot_on_error:
                        file, lineno = _get_lineno(inspect.stack())
                        file_name = (
                            f"{self.page_name}__{self.name_in_page}"
                            f"{f'__{file}' if file else ''}"
                            f"{f'__{lineno}' if lineno else ''}"
                        )
                        file_name = _clean_filename(file_name)
                        file_path = os.path.join(BotConfig.output_folder, file_name)
                        try:
                            if self.browser.driver.capabilities.get("browserName", "") == "firefox":
                                # switch to the main content before taking a screenshot
                                self.browser.driver.switch_to.default_content()
                            self.browser.capture_page_screenshot(file_path)
                            logger.debug(f"Screenshot saved to {file_path}")
                            attach_file_to_exception(e, file_path)
                        except Exception as ex:
                            report_error(ex, "Failed to capture screenshot")
                            logger.debug(f"Failed to capture screenshot due to error : {str(ex)}")
                    raise
                return result
        return lambda: None

    return wrapper


class BugCatcherMeta(type):
    """Metaclass for bug catcher."""

    def __new__(cls, name: str, bases: tuple[type, ...], dct: dict[str, Any]) -> "BugCatcherMeta":
        """New method for metaclass."""
        for attr_name, attr_value in dct.items():
            if callable(attr_value) and attr_name != "__init__":
                dct[attr_name] = _attach_browser_data_if_error(attr_value)
        return super().__new__(cls, name, bases, dct)
