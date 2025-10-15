"""Contains the EndpointElement class."""

import html
import json
from typing import Any
from SeleniumLibrary.errors import NoOpenBrowser

from requests import (
    HTTPError,
    JSONDecodeError,
    ReadTimeout,
    RequestException,
    Response,
    Timeout,
    TooManyRedirects,
)

from .. import logger

from ..exceptions import BadRequestError
import requests
from RPA.Browser.Selenium import Selenium
from ..bug_catcher_meta import BugCatcherMeta
from typing import Optional


class EndpointElement(metaclass=BugCatcherMeta):
    """This is an Endpoint Element used to build each Page."""

    def __init__(
        self,
        url: str,
        browser: Selenium,
        headers: Optional[dict] = None,
        return_response_object: bool = False,
        default_timeout: int = 60,
    ) -> None:
        """
        Initializes an EndpointElement instance with a specified URL and optional headers.

        Args:
            url (str): The request URL for the endpoint. Must be a valid URL.
            headers (dict, optional): A dictionary of additional headers to include
                in the session. These headers will override the default headers
                extracted from the browser, such as "User-Agent".
        """
        self.url = url
        self.headers = headers or {}
        self.return_response_object = return_response_object
        self.default_timeout: int = default_timeout

        self.browser: Selenium = browser
        self.session: requests.Session = requests.Session()

        default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        self.session.headers.update({**default_headers, **self.headers})

        self.name_in_page = None
        self.page_name = None

    def __set_name__(self, owner, name):
        """Called when the attribute is set in the class.

        Args:
            owner: The class where this descriptor is defined.
            name: The name of the attribute.
        """
        self.name_in_page = name
        self.page_name = owner.__name__

    def __update_session_with_browser_cookies(self):
        """Updates the session with cookies from the browser instance, if the browser is open."""
        try:
            self.session.cookies.update(self.browser.get_cookies(as_dict=True))
        except NoOpenBrowser:
            logger.debug("No browser open, did not update session cookies.")

    def __handle_response(self, response: Response) -> dict[str, Any]:
        """Handles the HTTP response, checking for errors and returning the response content.

        Args:
            response: An HTTPX Response object.

        Returns:
            The JSON content if the response is in JSON format, otherwise the response text.
        """
        try:
            response.raise_for_status()
            if self.return_response_object:
                return response
            text = html.unescape(response.text)
            return json.loads(text) if "application/json" in response.headers.get("Content-Type", "") else text
        except (
            HTTPError,
            JSONDecodeError,
            ReadTimeout,
            RequestException,
            Timeout,
            TooManyRedirects,
        ) as exc:
            logger.error(f"An error occurred while requesting: {exc.response.status_code} - {exc.response.text}")
            raise BadRequestError(str(exc), exc)

    def __request(self, method: str, **kwargs) -> dict[str, Any]:
        """Generic request method that ensures cookies are updated before sending requests."""
        logger.debug(f"Initiating {method.upper()} request to URL: {self.url}.")
        self.__update_session_with_browser_cookies()
        response = self.session.request(method=method, url=self.url, timeout=self.default_timeout, **kwargs)
        return self.__handle_response(response)

    def get(
        self,
        headers: dict[str, str] = {},
        cookies: dict[str, str] = {},
        params: dict[str, Any] = {},
    ) -> dict[str, Any]:
        """Sends a GET request to the specified URL with optional headers, cookies, and parameters.

        Args:
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.
            params: A dictionary containing the request parameters. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful.
        """
        return self.__request("GET", headers=headers, cookies=cookies, params=params)

    def patch(
        self,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] = {},
        cookies: dict[str, str] = {},
        params: dict[str, Any] = {},
    ) -> dict[str, Any]:
        """Sends a PATCH request to the specified URL with optional data, JSON, headers, cookies, and parameters.

        Args:
            data: The data to send in the request body. Defaults to None.
            json: The JSON data to send in the request body. Defaults to None.
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.
            params: A dictionary containing the request parameters. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful.
        """
        return self.__request(
            "PATCH",
            data=data,
            json=json,
            headers=headers,
            cookies=cookies,
            params=params,
        )

    def post(
        self,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] = {},
        cookies: dict[str, str] = {},
        params: dict[str, Any] = {},
    ) -> dict[str, Any]:
        """Sends a POST request to the specified URL with optional data, JSON, headers, cookies, and parameters.

        Args:
            data: The data to send in the request body. Defaults to None.
            json: The JSON data to send in the request body. Defaults to None.
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.
            params: A dictionary containing the request parameters. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful.
        """
        return self.__request(
            "POST",
            data=data,
            json=json,
            headers=headers,
            cookies=cookies,
            params=params,
        )

    def put(
        self,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] = {},
        cookies: dict[str, str] = {},
        params: dict[str, Any] = {},
    ) -> dict[str, Any]:
        """Sends a PUT request to the specified URL with optional data, JSON, headers, cookies, and parameters.

        Args:
            data: The data to send in the request body. Defaults to None.
            json: The JSON data to send in the request body. Defaults to None.
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.
            params: A dictionary containing the request parameters. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful
        """
        return self.__request("PUT", data=data, json=json, headers=headers, cookies=cookies, params=params)

    def delete(self, headers: dict[str, str] = {}, cookies: dict[str, str] = {}) -> dict[str, Any]:
        """Sends a DELETE request to the specified URL with optional headers and cookies.

        Args:
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful
        """
        return self.__request("DELETE", headers=headers, cookies=cookies)
