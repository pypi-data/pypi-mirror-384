# T_page_object 📦

> **A Python package for taking an object oriented approach
            when interacting with web pages and their elements .**

## 📑 Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage Example](#usage-example)
- [Performance Suite](#performance-suite)
- [API Documentation](#api-documentation)
- [License](#license)

## Overview
This package provides various modules and classes for creating portals, web pages and web elements.
            
There are also usable web elements that have commonly used methods built in.

## Installation
```bash
pip install t-page-object
```

## Usage Example
For detailed examples, please refer to our
            [quick start page](https://www.notion.so/thoughtfulautomation/T-Page-Object-126f43a78fa480e39a1af8f99f93affe).

### 
## Performance Suite

The package includes a performance testing suite that measures the execution time of various page interactions. This helps in identifying performance bottlenecks and ensuring optimal performance when interacting with web elements.

### What is the Performance Suite?

The performance suite is a collection of tests that measure the execution time for:
- Page loading
- Element interactions (clicks, form filling, etc.)
- DOM manipulation
- Alert handling

Tests are run against various demo websites to provide a comprehensive performance profile.

### Running the Performance Suite

To run the performance suite:

```bash
# Make sure you have the development requirements installed
pip install -r dev_requirements.txt

# Run the performance tests
CAPTCHA_GURU_API_KEY=XXX PYTHONPATH=. python performance/runner.py
```

Results are saved to `performance/outputs/` with timestamps for tracking performance over time.

When running in CI/CD environments, you can use a Selenium Grid with:

```bash
PYTHONPATH=. SELENIUM_GRID_URL=http://localhost:4444/wd/hub python performance/runner.py
```

## API Documentation

---

## Base
### Module: `t_page_object.base`

_Base objects package for t_page_object._

### Module: `t_page_object.base.base_app`

_Module for BaseApp class._

- **Class:** `BaseApp`
  > Base class for application or portal objects and their configuration.
  - **Method:** `open_browser`
    > Open browser and set Selenium options.
### Module: `t_page_object.base.base_page`

_Contains the BasePage class which is the parent class for all page objects in the project._

- **Class:** `BasePage`
  > Base page class for all page objects in the project.
  - **Method:** `get_element_from_shadow_roots`
    > Get element from nested shadow roots.

        Args:
            roots: The css locators of the shadow root elements, in hierarchal order.
            element_css: The css locator of the element to find.

        Returns:
            The WebElement of the element found.
        
  - **Method:** `visit`
    > Navigate to the base page URL.
  - **Method:** `wait_for_new_window_and_switch`
    > Function for waiting and switching to new window.

        Args:
            old_window_handles: The list of window handles before the new window is opened.

        Returns:
            The new window handle.
        
  - **Method:** `wait_page_load`
    > Wait for the page to load by waiting for the verification element to load.

        timeout: The maximum time to wait for the element to be present, in seconds.
        
### Module: `t_page_object.base.endpoint_element`

_Contains the EndpointElement class._

- **Class:** `EndpointElement`
  > This is an Endpoint Element used to build each Page.
  - **Method:** `delete`
    > Sends a DELETE request to the specified URL with optional headers and cookies.

        Args:
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful
        
  - **Method:** `get`
    > Sends a GET request to the specified URL with optional headers, cookies, and parameters.

        Args:
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.
            params: A dictionary containing the request parameters. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful.
        
  - **Method:** `patch`
    > Sends a PATCH request to the specified URL with optional data, JSON, headers, cookies, and parameters.

        Args:
            data: The data to send in the request body. Defaults to None.
            json: The JSON data to send in the request body. Defaults to None.
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.
            params: A dictionary containing the request parameters. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful.
        
  - **Method:** `post`
    > Sends a POST request to the specified URL with optional data, JSON, headers, cookies, and parameters.

        Args:
            data: The data to send in the request body. Defaults to None.
            json: The JSON data to send in the request body. Defaults to None.
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.
            params: A dictionary containing the request parameters. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful.
        
  - **Method:** `put`
    > Sends a PUT request to the specified URL with optional data, JSON, headers, cookies, and parameters.

        Args:
            data: The data to send in the request body. Defaults to None.
            json: The JSON data to send in the request body. Defaults to None.
            headers: A dictionary containing the request headers. Defaults to an empty dictionary.
            cookies: A dictionary containing the request cookies. Defaults to an empty dictionary.
            params: A dictionary containing the request parameters. Defaults to an empty dictionary.

        Returns:
            The response content if the request is successful
        
### Module: `t_page_object.base.ui_element`

_Contains the UIElement class._

- **Class:** `UIElement`
  > This is an UI Element used to build each Page.
  - **Method:** `format_xpath`
    > If using a dynamic xpath, this method formats the xpath string.

        Args:
            *args (list): The arguments to be used to format the xpath.
            **kwargs (dict): The keyword arguments to be used to format the
        
  - **Method:** `wait_element_load`
    > 
        Wait for element to load.

        Args:
            timeout (int, optional): The maximum time to wait for the element to be present, in seconds.
                Defaults to None. Overwrites apps inherent timeout if set.

        Returns:
            bool: True if element is visible, False not found and wait is False otherwise.

        Raises:
            AssertionError: If element is not visible and wait is True.
        

---

## Bot_config
### Module: `t_page_object.bot_config`

_Congifuration module for the t_page_object package._

- **Class:** `BotConfig`
  > Class for configuration.

---

## Elements
### Module: `t_page_object.elements`

_Module for all base ui components._

### Module: `t_page_object.elements.button_element`

_Button element module._

- **Class:** `ButtonElement`
  > Standard button element.
  - **Method:** `click`
    > Main click method for button element.

        Checks if button is dev_save_sensitive and if dev_safe_mode is enabled.
        
  - **Method:** `click_button`
    > Redirects to click method.
  - **Method:** `click_button_if_visible`
    > Redirects to click method.
  - **Method:** `click_button_when_visible`
    > Redirects to click method.
  - **Method:** `click_element`
    > Redirects to click method.
  - **Method:** `click_element_if_visible`
    > Redirects to click method.
  - **Method:** `click_element_when_clickable`
    > Redirects to click method.
  - **Method:** `click_element_when_visible`
    > Redirects to click method.
### Module: `t_page_object.elements.checkbox_element`

_Checkbox element module._

- **Class:** `CheckboxElement`
  > Checkbox element.
  - **Method:** `select`
    > Selects the checkbox element.
### Module: `t_page_object.elements.container_element`

_Class for container elements._

- **Class:** `ContainerElement`
  > Container element. Used to hold multiple text elements.
  - **Method:** `check_if_all_elements_contain_value`
    > Get text for each attribute in object with matching id.
  - **Method:** `get_text_values`
    > Get text for each element with id matching class attribute.

        Args:
            cls (Type[TO]): The class to use for the object.

        Returns:
            Instance of input class with text values.
        
  - **Method:** `set_text_values`
    > Sets text for each element with id matching class attribute.

        Args:
            cls (Type[TO]): The object to use for the text values.
        
### Module: `t_page_object.elements.dropdown_element`

_Dropdown element module._

- **Class:** `DropdownElement`
  > Standard dropdown element.
  - **Method:** `click_and_select_option`
    > Selects an option from the dropdown list based on the provided text.

        The dropdown list is clicked to open the list and the option is selected.

        Args:
            text_to_find (str): The text of the option to be selected from the dropdown list.
            match_strategy (Literal["exact", "contains"], optional): The strategy for matching the text.
                "exact" for exact match (default), "contains" for partial match. Defaults to "exact".

        Returns:
            bool: Is the requested option present in the list.
        
  - **Method:** `get_selected_option`
    > Gets the selected option.
  - **Method:** `type_and_enter`
    > Selects an option from the dropdown list based on the provided text.

        The text is input into the dropdown list input and the Enter key is pressed to select the option.

        Args:
            text_to_enter (str): The text/s of the option to be selected from the dropdown list.
            option_tag (str): The tag used for the different options. Defaults to 'li'.

        Returns:
            None
        
### Module: `t_page_object.elements.iframe_element`

_Frame element module._

- **Class:** `IFrameElement`
  > Class for frame element model.
  - **Method:** `select_iframe`
    > Select frame.
  - **Method:** `select_nested_iframe`
    > Select nested frame.

        Args:
            frames: list of frame locators
            from_base: bool, if True, unselects the current frame before selecting the nested frames
        
  - **Method:** `unselect_iframe`
    > Selects base frame.
### Module: `t_page_object.elements.image_element`

_Image element module._

- **Class:** `ImageElement`
  > Image element.
  - **Method:** `download_image`
    > Download images using RPA.HTTP and return the local path.

        Args:
            download_path (str, optional): The path to save the downloaded image. Defaults to output_folder.

        Returns:
            str: The path of the downloaded image.
        
### Module: `t_page_object.elements.input_element`

_Input element module._

- **Class:** `InputElement`
  > Input element.
  - **Method:** `click_and_input_text`
    > Input text into element.
  - **Method:** `get_input_value`
    > Get input value.
  - **Method:** `input_text_and_check`
    > 
        Inputs the given text into an element and verifies the input.

        Args:
            text (str): The text to input into the element.
            tries (int, optional): The number of attempts to verify the text input. Defaults to 5.

        Returns:
            None
        
### Module: `t_page_object.elements.table_element`

_Table element module._

- **Class:** `TableElement`
  > Table element.
  - **Method:** `get_summary_table_data`
    > Extracts and structures data from an HTML summary table into a list of dictionaries.

        This method locates the table headers and body rows, then iterates over them to extract the data.
        Each row of the table is represented as a dictionary.

        Returns:
            list: A list of dictionaries, where each dictionary represents a row in the table.
                Each dictionary key is a column header, and each value is the corresponding data
                from that column in the row.
        
  - **Method:** `get_table_data`
    > Extracts data from an HTML table.

        This method locates table headers and body elements, then iterates over them to extract and structure the data
        into a dictionary.

        Args:
            table_orientation (str): The orientation of the table. Can be either 'vertical' or 'horizontal'.
                Defaults to 'vertical'.

        Returns:
            list: A list where each item is a dict representing a table. Each dict has column headers
                as keys and a list for all column values
        
### Module: `t_page_object.elements.table_row_element`

_Table Row element module._

- **Class:** `TableRowElement`
  > Class for TextElement element model.
  - **Method:** `get_row_values`
    > Get Element value.
### Module: `t_page_object.elements.text_element`

_This module contains the TextElement class for the text element model._

- **Class:** `TextElement`
  > Input element.
  - **Method:** `get_clean_text`
    > Get text from element and clean.

---

## Selenium_manager
### Module: `t_page_object.selenium_manager`

_Create a singleton manager to ensure a single instance of Selenium._

- **Class:** `SeleniumManager`
  > Singleton manager to ensure a single instance of Selenium.
