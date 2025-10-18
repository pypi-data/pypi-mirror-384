import re

from hamcrest import has_length, assert_that, greater_than_or_equal_to
from playwright.sync_api import expect
from reportportal_client import step

from codemie_test_harness.tests.ui.pageobject.base_page import BasePage
from codemie_test_harness.tests.ui.pageobject.datasources.datasource_sidebar import (
    DataSourceSidebar,
)
from codemie_test_harness.tests.ui.test_data.datasource_test_data import (
    DATAS_SOURCE_COLUMN_LIST,
)


class DataSourcePage(BasePage):
    """Data Sources page object with property-based element locators."""

    page_url = "#/data-sources"

    def __init__(self, page):
        super().__init__(page)
        self.sidebar = DataSourceSidebar(page)

    # -----------------
    # Page Elements
    # -----------------

    @property
    def create_datasource_button(self):
        """'Create Datasource' button."""
        return self.page.locator('button:has-text("Create Datasource")')

    @property
    def table(self):
        """Datasource table."""
        return self.page.locator("table")

    @property
    def table_rows(self):
        """Table data rows."""
        return self.table.locator("tbody tr")

    def table_columns_names(self, column: str):
        """Table data column names."""
        return self.table.locator(".text-left:not(.text-gray-50)").filter(
            has_text=re.compile(f"^{re.escape(column)}$")
        )

    @property
    def row_menu_view_details_button(self):
        return self.page.locator("span.text-left.grow").filter(has_text="View Details")

    @property
    def row_menu_edit_button(self):
        return self.page.locator("span.text-left.grow").filter(has_text="Edit")

    @property
    def row_menu_copy_id_button(self):
        return self.page.locator("span.text-left.grow").filter(has_text="Copy ID")

    @property
    def row_menu_export_button(self):
        return self.page.locator("span.text-left.grow").filter(has_text="Export")

    @property
    def row_menu_delete_button(self):
        return self.page.locator("span.text-left.grow").filter(has_text="Delete")

    @property
    def row_menu_full_reindex_button(self):
        return self.page.locator("span.text-left.grow").filter(has_text="Full Reindex")

    @property
    def row_menu_incremental_index_button(self):
        return self.page.locator("span.text-left.grow").filter(
            has_text="Incremental Index"
        )

    # -------------------------------
    # Navigation methods
    # -------------------------------
    @step
    def navigate_to(self):
        """
        Navigate to the DataSource page.

        Returns:
            self: Returns the page object for method chaining
        """
        self.page.goto(self.page_url)
        self.wait_for_page_load()

        return self

    # -----------------
    # Table Methods
    # -----------------
    @step
    def get_table_row_by_name(self, name: str):
        """Get the row as locator by datasource name."""
        return self.page.locator("tbody tr:has(td:nth-child(1) span.font-bold)").filter(
            has_text=name
        )

    def get_cell_in_row(self, row_locator, col_idx):
        return row_locator.locator(f"td:nth-child({col_idx})")

    def get_status_in_row(self, row_locator):
        return self.get_cell_in_row(row_locator, 8).locator("div.inline-flex")

    def get_project_in_row(self, row_locator):
        return self.get_cell_in_row(row_locator, 2).locator("span")

    def get_type_in_row(self, row_locator):
        return self.get_cell_in_row(row_locator, 3)

    def get_created_by_in_row(self, row_locator):
        return self.get_cell_in_row(row_locator, 4).locator("span")

    @step
    def click_datasource_row_by_name(self, name: str):
        self.get_table_row_by_name(name).locator("span.font-bold").click()
        return self

    def get_row_action_menu_button(self, datasource_name: str):
        """
        Returns the 3-dot menu button locator for a row by datasource name.
        """
        # Find the row with the given datasource name,
        # then get 3-dot menu button in the last column.
        row = self.get_table_row_by_name(datasource_name)
        return row.locator("td:last-child button")

    @step
    def open_row_action_menu(self, datasource_name: str):
        """
        Opens the 3-dot actions menu for a row by datasource name.
        """
        btn = self.get_row_action_menu_button(datasource_name)
        expect(btn).to_be_visible()
        btn.click()
        return self

    @step
    def click_row_action(self, action_text: str):
        """
        Clicks a menu item in the currently open 3-dot menu by the visible text.
        """
        self.page.locator("button").filter(has_text=action_text).click()
        return self

    @step
    def open_and_select_row_action(self, datasource_name: str, action_text: str):
        """
        Opens the 3-dot menu in the specified row and selects a menu action.
        """
        self.open_row_action_menu(datasource_name)
        self.click_row_action(action_text)
        return self

    # -----------------
    # Verification Methods
    # -----------------

    @step
    def should_see_create_datasource_button(self):
        expect(self.create_datasource_button).to_be_visible()
        return self

    @step
    def should_see_table_rows(self, minimum_count: int = 1):
        expect(self.table_rows.first).to_be_visible()
        assert_that(
            self.table_rows.all(), has_length(greater_than_or_equal_to(minimum_count))
        )
        return self

    @step
    def should_see_table_column_names(self):
        for column in DATAS_SOURCE_COLUMN_LIST:
            column_name = self.table_columns_names(column)
            expect(column_name).to_be_visible()

    @step
    def should_see_datasource_with_name(self, name: str):
        expect(self.get_table_row_by_name(name)).to_be_visible()
        return self

    @step
    def should_see_pagination(self, page: int = 1):
        expect(self.pagination_block).to_be_visible()
        expect(self.pagination_page_button(page)).to_be_visible()
        expect(self.show_per_page_dropdown).to_be_visible()
        expect(self.show_per_page_label).to_be_visible()
        return self

    @step
    def should_see_table_row_with_values(
        self, name, status, project=None, type_=None, created_by=None, timeout=60000
    ):
        """
        Verifies that a table row exists for the given parameters, and has the expected status.
        Optionally checks project, type, created_by columns.
        """
        row = self.get_table_row_by_name(name)
        expect(row).to_be_visible(timeout=5000)

        if project is not None:
            expect(self.get_project_in_row(row)).to_have_text(project)
        if type_ is not None:
            expect(self.get_type_in_row(row)).to_have_text(type_)
        if created_by is not None:
            expect(self.get_created_by_in_row(row)).to_have_text(created_by)

        expect(self.get_status_in_row(row)).to_have_text(status, timeout=timeout)
        return self

    @step
    def should_see_edit_dropdown_values(self):
        expect(self.row_menu_view_details_button).to_be_visible()
        expect(self.row_menu_edit_button).to_be_visible()
        expect(self.row_menu_copy_id_button).to_be_visible()
        expect(self.row_menu_export_button).to_be_visible()
        expect(self.row_menu_delete_button).to_be_visible()
        return self

    @step
    def should_see_edit_dropdown_index_values(self):
        expect(self.row_menu_incremental_index_button).to_be_visible()
        expect(self.row_menu_full_reindex_button).to_be_visible()
        return self

    @step
    def should_see_edit_dropdown_full_reindex_value(self):
        expect(self.row_menu_full_reindex_button).to_be_visible()
        return self
