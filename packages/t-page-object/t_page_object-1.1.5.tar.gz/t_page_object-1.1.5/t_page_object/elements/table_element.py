"""Table element module."""
from RPA.Browser import Selenium
from selenium.webdriver.common.by import By

from ..base.ui_element import UIElement
from ..decorators import retry_if_stale_element_error


class TableElement(UIElement):
    """Table element."""

    def __init__(
        self,
        xpath: str,
        browser: Selenium,
        wait: bool = True,
        id: str = "",
        timeout: int | None = None,
        xpath_header: str = ".//thead",
        xpath_body: str = ".//tbody",
        xpath_header_cells: str = "",
        xpath_body_rows: str = "",
        xpath_body_cells: str = "",
    ) -> None:
        """Initialize the TableElement."""
        super().__init__(xpath, browser, wait, id, timeout)

        self.xpath_header = xpath_header
        self.xpath_body = xpath_body
        self.xpath_header_cells = xpath_header_cells or "//tr//th"
        self.xpath_body_rows = xpath_body_rows or "//tr"
        self.xpath_body_cells = xpath_body_cells or ".//td"

    @retry_if_stale_element_error
    def get_table_data(self, table_orientation: str = "vertical") -> list:
        """Extracts data from an HTML table.

        This method locates table headers and body elements, then iterates over them to extract and structure the data
        into a dictionary.

        Args:
            table_orientation (str): The orientation of the table. Can be either 'vertical' or 'horizontal'.
                Defaults to 'vertical'.

        Returns:
            list: A list where each item is a dict representing a table. Each dict has column headers
                as keys and a list for all column values
        """
        tables: list = []
        if table_orientation == "vertical":
            t_headers = self.find_element().find_elements(By.XPATH, self.xpath_header)
            t_bodies = self.find_element().find_elements(By.XPATH, self.xpath_body)
            for header, body in zip(t_headers, t_bodies):
                table: dict = {}
                columns = header.find_elements(By.XPATH, f".{self.xpath_header_cells}")
                for row in body.find_elements(By.XPATH, f".{self.xpath_body_rows}"):
                    t_data = row.find_elements(By.XPATH, self.xpath_body_cells)
                    for column, data in zip(columns, t_data):
                        if column.text.strip() not in table.keys():
                            table[column.text.strip()] = []
                        table[column.text.strip()].append(data.text.strip())
                tables.append(table)
        elif table_orientation == "horizontal":
            t_headers = self.find_element().find_elements(By.XPATH, self.xpath_header)
            t_bodies = self.find_element().find_elements(By.XPATH, self.xpath_body)
            for header, body in zip(t_headers, t_bodies):
                table = {}
                for row in body.find_elements(By.XPATH, f".{self.xpath_body_rows}"):
                    row_values = row.find_elements(By.XPATH, self.xpath_body_cells)
                    column, column_values = row_values[0], row_values[1:]
                    table[column.text.strip()] = [col.text.strip() for col in column_values]
                tables.append(table)
        else:
            raise ValueError(f"Invalid table orientation: {table_orientation}")

        return tables

    @retry_if_stale_element_error
    def get_summary_table_data(self) -> list:
        """Extracts and structures data from an HTML summary table into a list of dictionaries.

        This method locates the table headers and body rows, then iterates over them to extract the data.
        Each row of the table is represented as a dictionary.

        Returns:
            list: A list of dictionaries, where each dictionary represents a row in the table.
                Each dictionary key is a column header, and each value is the corresponding data
                from that column in the row.
        """
        table_data = []
        t_heads = self.find_element().find_elements(By.XPATH, f"{self.xpath_header}{self.xpath_header_cells}")
        rows = self.find_element().find_elements(By.XPATH, f"{self.xpath_body}{self.xpath_body_rows}")
        for row in rows:
            row_data = {}
            t_data = row.find_elements(By.XPATH, self.xpath_body_cells)
            for header, data in zip(t_heads, t_data):
                row_data[header.text.strip()] = data.text.strip()
            table_data.append(row_data)

        return table_data
