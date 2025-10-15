#!/usr/bin/env python
"""Tests for endpoint component methods."""

from t_page_object.selenium_manager import SeleniumManager
from tests.t_test_app import TestApp


class TestMethodsEndpoints:
    """Test methods for EndpointElements."""

    def setup_method(self):
        """Setup method."""
        self.browser = SeleniumManager.get_instance("test_app")
        self.app = TestApp(self.browser)

    def teardown_method(self):
        """Teardown method."""
        self.app.browser.close_browser()

    """Test methods for EndpointElements."""

    def test_endpoint_elements(self):
        """Test Endpoint elements."""
        self.app.endpoint_test_page.get_endpoint.get(params={"param": "Test Get Data"})
        self.app.endpoint_test_page.patch_endpoint.patch(data={"data": "Test Patch Data"})
        self.app.endpoint_test_page.post_endpoint.post(data={"data": "Test Post Data"})
        self.app.endpoint_test_page.put_endpoint.put(data={"data": "Test Put Data"})
        self.app.endpoint_test_page.delete_endpoint.delete()
