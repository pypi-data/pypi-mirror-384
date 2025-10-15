#!/usr/bin/env python
"""Tests for component methods in Firefox."""

from t_page_object.selenium_manager import SeleniumManager
from .t_test_app import TestApp, AlertApp
from t_object import ThoughtfulObject
import os
from pathlib import Path
from time import sleep
from t_page_object.bot_config import BotConfig


class Article(ThoughtfulObject):
    """Article class."""

    title: str = ""
    category: str = ""


class User(ThoughtfulObject):
    """User class."""

    username: str = "test user"
    password: str = "test password"


class TestMethodsFirefox:
    """Test methods in firefox."""

    @classmethod
    def setup_class(self):
        """Setup class."""
        self.remote_url = os.getenv("SELENIUM_GRID_URL")

        # We need this var for bitbucket pipelines sucessfull run
        self.executable_path = os.path.join(os.getcwd(), "geckodriver")
        if not os.path.exists(self.executable_path):
            self.executable_path = None

    def setup_method(self):
        """Setup method."""
        self.browser = SeleniumManager.get_instance("test_app")
        self.app = TestApp(self.browser)
        self.alert_app = AlertApp(self.browser)

    def teardown_method(self):
        """Teardown method."""
        self.app.browser.close_browser()

    def test_ui_elements_firefox(self):
        """Test UI elements in browser instance."""
        self.app.browser.open_browser(
            browser="firefox",
            url=self.app.ui_test_page.url,
            remote_url=self.remote_url,
            executable_path=self.executable_path,
        )
        self.app.browser.maximize_browser_window()
        self.app.ui_test_page.visit()
        self.app.ui_test_page.continue_button.format_xpath(name="Continue")
        self.app.ui_test_page.continue_button.is_element_visible(timeout=15)
        self.app.ui_test_page.continue_button.click()
        self.app.ui_test_page.search_button.wait_element_load(15)
        self.app.ui_test_page.search_button.is_element_visible()
        self.app.ui_test_page.search_button.click()
        self.app.ui_test_page.search_input.input_text_and_check("Robot")
        self.app.ui_test_page.search_go.click()
        self.app.ui_test_page.times_logo.wait_element_load(30)
        assert "New York Times homepage" == self.app.ui_test_page.times_logo.get_element_attribute("aria-label")
        self.app.ui_test_page.image.download_image()
        self.app.ui_test_page.article.get_text_values(Article)
        self.app.ui_test_page.section_button.click()
        self.app.ui_test_page.arts_cb.select()
        self.app.ui_test_page.sort_by_dd.click_and_select_option("NEWest", match_strategy="contains")
        assert "newest" == self.app.ui_test_page.sort_by_dd.get_selected_option()

        self.app.select_page.visit()
        assert self.app.select_page.select_dropdown.does_page_contain_element()

        self.app.select_page.select_dropdown.click_and_select_option("2")

        assert self.app.select_page.is_in_page()
        assert not self.app.ui_test_page.is_in_page()

        assert self.app.select_page.select_dropdown.is_element_visible()
        assert not self.app.ui_test_page.search_button.is_element_visible(timeout=1)

    def test_table_elements_firefox(self):
        """Test Table elements."""
        self.app.browser.open_browser(
            browser="firefox",
            url=self.app.table_page.url,
            remote_url=self.remote_url,
            executable_path=self.executable_path,
        )
        self.app.table_page.visit()
        self.app.table_page.table.get_table_data()
        self.app.table_page.table.get_table_data("horizontal")
        self.app.table_page.table.get_summary_table_data()
        self.app.table_page.table_row.get_row_values()

    def test_headless_table_elements_firefox(self):
        """Test Table elements."""
        # Arrange
        self.app.browser.open_browser(
            browser="firefox",
            url=self.app.headless_table_page.url,
            remote_url=self.remote_url,
            executable_path=self.executable_path,
        )

        # Act
        self.app.headless_table_page.visit()
        table_data = self.app.headless_table_page.table.get_table_data()
        table_data_horizontal = self.app.headless_table_page.table.get_table_data("horizontal")
        table_summary = self.app.headless_table_page.table.get_summary_table_data()
        row_value = self.app.headless_table_page.table_row.get_row_values()

        # Assert
        assert len(table_data[0]) == 5 and len(table_data[0]["Baseline characteristic"]) == 24
        assert table_data_horizontal[0]["Single"] == ["13", "26", "11", "22", "17", "34", "41", "27"]
        assert table_summary[3]["Guided self-help"] == "25"
        assert row_value == ["  Female 25 50 20 40 23 46 68 45"]

    def test_container_element_firefox(self):
        """Test container element."""
        self.app.browser.open_browser(
            browser="firefox",
            url=self.app.login_page.url,
            remote_url=self.remote_url,
            executable_path=self.executable_path,
        )
        self.app.login_page.visit()
        self.app.login_page.login_container.set_text_values(User())
        assert self.app.login_page.login_container.check_if_all_elements_contain_value()

    def test_alert_popup_firefox(self):
        """Test alert popup."""
        BotConfig.handle_alerts = True
        self.alert_app.browser.open_browser(
            browser="firefox",
            url=self.alert_app.alert_page.url,
            remote_url=self.remote_url,
            executable_path=self.executable_path,
        )
        self.alert_app.alert_page.visit()
        self.alert_app.alert_page.alert_box_button.click()
        self.alert_app.alert_page.confirm_alert_button.click()
        self.alert_app.alert_page.promp_alert_button.click()

    def test_modal_firefox(self):
        """Test modal."""
        BotConfig.handle_alerts = False
        self.app.browser.open_browser(
            browser="firefox",
            url=self.app.modal_page.url,
            remote_url=self.remote_url,
            executable_path=self.executable_path,
        )
        self.app.modal_page.visit()
        self.app.modal_page.modal_button.click()
        sleep(2)
        self.app.modal_page.search_button.click()

    def test_screenshot_firefox(self):
        """Test screenshot feature."""
        screenshot_path_png = Path(os.getcwd()) / "test_screenshot.png"
        self.app.browser.open_browser(
            browser="firefox",
            url=self.app.login_page.url,
            remote_url=self.remote_url,
            executable_path=self.executable_path,
        )
        self.app.login_page.visit()
        self.app.login_page.screenshot(filename=screenshot_path_png)
        assert os.path.exists(screenshot_path_png)
        os.remove(screenshot_path_png)

        screenshot_path_webp = Path(os.getcwd()) / "test_screenshot.webp"
        self.app.login_page.screenshot(filename=screenshot_path_webp, convert_to_webp=True)
        assert os.path.exists(screenshot_path_webp)
        os.remove(screenshot_path_webp)

        screenshot_path_png = Path(os.getcwd()) / "test_screenshot.png"
        self.app.login_page.screenshot(locator="//img", filename=screenshot_path_png)
        assert os.path.exists(screenshot_path_png)
        os.remove(screenshot_path_png)

        screenshot_path_webp = Path(os.getcwd()) / "test_screenshot.webp"
        self.app.login_page.screenshot(locator="//img", filename=screenshot_path_webp, convert_to_webp=True)
        assert os.path.exists(screenshot_path_webp)
        os.remove(screenshot_path_webp)
