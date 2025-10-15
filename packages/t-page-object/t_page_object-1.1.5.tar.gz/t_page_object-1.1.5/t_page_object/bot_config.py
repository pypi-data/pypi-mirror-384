"""Congifuration module for the t_page_object package."""
from pathlib import Path


class BotConfig:
    """Class for configuration."""

    output_folder = Path().cwd() / "output"
    dev_safe_mode = True
    capture_screenshot_on_error = True
    default_timeout = 10
    handle_alerts = False
    alert_handling_option = "ACCEPT"
    close_modals = True
    modal_button = None
    enable_logging = True

    @classmethod
    def configure(cls, **kwargs):
        """Set configuration variables.

        Args:
            output_folder: The folder where the output files are saved. Defaults to "output"
            dev_safe_mode: If True, the bot will run in safe mode. Defaults to True.
            capture_screenshot_on_error: If True, the bot will capture a
                screenshot if an error occurs. Defaults to True.
            handle_alerts: If True, the bot will handle alerts. Defaults to False.
            alert_handling_option: The default option for handling alerts.
                Options: "ACCEPT", "DISMISS", "LEAVE". Defaults to "ACCEPT".
            close_modals: If True, the bot will attempt to close modals if an element click is intercepted.
            modal_button: The text to look for in a button (ex. "Accept", "Dismiss" etc.). Defaults to None
            enable_logging: If True, logging will be enabled. Defaults to True.

        Raises:
            AttributeError: If an invalid configuration option is provided.
        """
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
            else:
                raise AttributeError(f"Invalid configuration option: {key}")
