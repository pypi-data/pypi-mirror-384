"""Image element module."""

import os

from RPA.HTTP import HTTP  # type: ignore

from ..base.ui_element import UIElement
from ..bot_config import BotConfig
from ..decorators import retry_if_stale_element_error


class ImageElement(UIElement):
    """Image element."""

    @retry_if_stale_element_error
    def download_image(self, download_path: str = str(BotConfig.output_folder)) -> str:
        """Download images using RPA.HTTP and return the local path.

        Args:
            download_path (str, optional): The path to save the downloaded image. Defaults to output_folder.

        Returns:
            str: The path of the downloaded image.
        """
        http = HTTP()
        url = self.get_element_attribute("src")
        filename = url.split("/")[-1].split("?")[0]  # Basic cleaning to remove URL parameters
        filepath = os.path.join(download_path, filename)
        http.download(url, filepath)
        return filepath
