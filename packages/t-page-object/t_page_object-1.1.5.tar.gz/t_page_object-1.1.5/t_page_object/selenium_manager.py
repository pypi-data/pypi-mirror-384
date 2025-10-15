"""Create a singleton manager to ensure a single instance of Selenium."""

from RPA.Browser.Selenium import Selenium  # type: ignore


class SeleniumManager:
    """Singleton manager to ensure a single instance of Selenium."""

    _portal_instances: dict[str, Selenium] = {}

    @classmethod
    def get_instance(cls: Selenium, instance_tag: str) -> Selenium:
        """Get the instance of Selenium for the calling module. If it does not exist, create it."""
        if instance_tag not in cls._portal_instances:
            cls._portal_instances[instance_tag] = Selenium()

        return cls._portal_instances[instance_tag]
