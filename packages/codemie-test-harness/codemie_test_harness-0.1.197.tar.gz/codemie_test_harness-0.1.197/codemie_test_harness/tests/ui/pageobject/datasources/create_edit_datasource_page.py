from typing import Optional

from playwright.sync_api import expect
from reportportal_client import step

from codemie_test_harness.tests.test_data.google_datasource_test_data import (
    GOOGLE_DOC_URL,
    GOOGLE_GUIDE_URL,
)
from codemie_test_harness.tests.ui.pageobject.base_page import BasePage
from codemie_test_harness.tests.ui.pageobject.components.project_selector import (
    ProjectSelector,
)
from codemie_test_harness.tests.ui.pageobject.datasources.datasource_sidebar import (
    DataSourceSidebar,
)
from codemie_test_harness.tests.ui.test_data.datasource_test_data import (
    DataSourceType,
    SUMMARIZATION_METHODS_LIST,
    EMBEDDING_MODELS_LIST,
    DATA_SOURCE_TYPES_LIST,
    FILE_INSTRUCTIONS,
    GOOGLE_INSTRUCTIONS,
    GOOGLE_EXAMPLE,
    EMPTY_NAME_ERROR,
    EMPTY_DESCRIPTION_ERROR,
    EMPTY_REPO_LINK_ERROR,
    EMPTY_BRANCH_ERROR,
    EMPTY_CQL_ERROR,
    EMPTY_JQL_ERROR,
    EMPTY_FILE_ERROR,
    EMPTY_GOOGLE_LINK_ERROR,
)
from codemie_test_harness.tests.utils.base_utils import get_random_name


class CreateEditDatasourcePage(BasePage):
    """Create Data Source page object with property-based element locators."""

    page_url = "/#/data-sources/create"

    def __init__(self, page):
        super().__init__(page)
        self.sidebar = DataSourceSidebar(page)
        self.selector = ProjectSelector(page)

    # -----------------
    # Page Elements
    # -----------------

    @property
    def back_button(self):
        return self.page.locator("button svg").nth(0).locator("xpath=..")

    @property
    def save_reindex_button(self):
        return self.page.locator("button:has-text('Save & Reindex')")

    @property
    def shared_with_project_switch(self):
        return self.page.locator("input#projectSpaceVisible + span")

    @property
    def name_input(self):
        return self.page.locator("input#name")

    @property
    def disabled_name_input(self):
        return self.page.locator("input#name[disabled]")

    @property
    def error_name_input(self):
        return self.page.locator('label:has(input[name="name"]) .input-error-message')

    @property
    def description_input(self):
        return self.page.locator("textarea#description")

    @property
    def error_description_input(self):
        return self.description_input.locator(" + div")

    @property
    def datasource_type_selector(self):
        return self.page.locator('span#indexType input[type="text"]')

    @property
    def datasource_type_dropdown(self):
        return self.page.locator("span#indexType button")

    @property
    def integration_input(self):
        return self.page.locator('span.p-autocomplete[id^="pr_id_"]')

    @property
    def add_integration_button(self):
        return self.page.locator('button:has-text("Add User Integration")')

    @property
    def integration_dropdown(self):
        return self.integration_input.locator("button")

    def dropdown_values(self, value: str):
        return self.page.locator(f'li:has-text("{value}")')

    # -------------------------------
    # Navigation methods
    # -------------------------------
    @step
    def navigate_to(self):
        """
        Navigate to the Create DataSource page.

        Returns:
            self: Returns the page object for method chaining
        """
        self.page.goto(self.page_url)
        self.wait_for_page_load()

        return self

    # -------------------------------
    # Git DataSource Type Elements
    # -------------------------------

    @property
    def summarization_method_input(self):
        return self.page.locator('span#repoIndexType input[type="text"]')

    @property
    def summarization_method_dropdown(self):
        return self.page.locator("span#repoIndexType button")

    @property
    def repo_link_input(self):
        return self.page.locator("input#repoLink")

    @property
    def error_repo_link_input(self):
        return self.page.locator(
            'label:has(input[name="repoLink"]) .input-error-message'
        )

    @property
    def branch_input(self):
        return self.page.locator("input#repoBranch")

    @property
    def error_branch_input(self):
        return self.page.locator('label:has(input[name="branch"]) .input-error-message')

    @property
    def files_filter_input(self):
        return self.page.locator("textarea#filesFilter")

    @property
    def embeddings_model_input(self):
        return self.page.locator('span#embeddingsModel input[type="text"]')

    @property
    def embeddings_model_dropdown(self):
        return self.page.locator("span#embeddingsModel button")

    # -------------------------------
    # Confluence DataSource Type Elements
    # -------------------------------

    @property
    def cql_query_input(self):
        return self.page.locator("input#cql")

    @property
    def error_cql_query_input(self):
        return self.page.locator('label:has(input[name="cql"]) .input-error-message')

    # -------------------------------
    # Jira DataSource Type Elements
    # -------------------------------

    @property
    def jql_query_input(self):
        return self.page.locator("input#jql")

    @property
    def error_jql_query_input(self):
        return self.page.locator('label:has(input[name="jql"]) .input-error-message')

    # -------------------------------
    # File DataSource Type Elements
    # -------------------------------

    @property
    def select_file_button(self):
        return self.page.locator("button:has-text('Select file')")

    @property
    def input_file(self):
        return self.page.locator('input[type="file"]')

    @property
    def remove_file_icon(self):
        return self.page.locator("svg.cursor-pointer")

    @property
    def add_file_button(self):
        return self.page.locator("button:has-text('Add file')")

    @property
    def files_info_text(self):
        return self.page.locator(".mb-4 div.flex.text-text-secondary.text-xs span")

    @property
    def error_files_info_text(self):
        return self.page.locator(".mb-4 .text-fire-50")

    @property
    def file_input_field(self):
        return self.page.locator("div.text-text-secondary.ml-2 ")

    @property
    def csv_separator_input(self):
        return self.page.locator(
            "span.p-autocomplete[id^='pr_id_'] input[name='csvSeparator']"
        )

    @property
    def csv_separator_dropdown_button(self):
        return self.page.locator(
            "span.p-autocomplete[id^='pr_id_'] button[aria-label='Choose']"
        )

    @property
    def csv_start_row_input(self):
        return self.page.locator("input[name='csvStartRow']")

    @property
    def csv_rows_per_document_input(self):
        return self.page.locator("input[name='csvRowsPerDocument']")

    # -------------------------------
    # Google DataSource Type Elements
    # -------------------------------

    @property
    def google_query_input(self):
        return self.page.locator("input#googleDoc")

    @property
    def error_google_query_input(self):
        return self.page.locator(
            'label:has(input[name="googleDoc"]) .input-error-message'
        )

    @property
    def google_instructions(self):
        return self.page.locator(".mb-4 div.flex.text-text-secondary.text-xs span")

    # -----------------
    # Action Methods
    # -----------------
    @step
    def fill_name(self, value: str):
        self.name_input.fill(value)
        return self

    @step
    def fill_description(self, value: str):
        self.description_input.fill(value)
        return self

    @step
    def select_project(self, value: str):
        self.project_multiselect.click()
        self.dropdown_values(value).click()
        return self

    @step
    def toggle_shared_with_project(self):
        self.shared_with_project_switch.click()
        return self

    @step
    def select_datasource_type(self, value: str):
        self.datasource_type_dropdown.click()
        self.dropdown_values(value).click()
        return self

    @step
    def select_integration(self, value: str):
        self.integration_dropdown.click()
        self.dropdown_values(value).click()
        return self

    @step
    def click_create(self):
        self.create_button.click()
        return self

    @step
    def click_cancel(self):
        self.cancel_button.click()
        return self

    def _base_create_datasource(
        self,
        name: Optional[str],
        project_name: Optional[str],
        description: Optional[str],
        datasource_type: DataSourceType,
        shared: bool = False,
        integration: Optional[str] = None,
    ):
        """
        Fills common fields for any DataSource type
        (name, description, project, type, shared, integration) but does not click 'Create'.

        Args:
            name: Optional[name], defaults to random if not provided
            project_name: Optional[str], selects a project if provided
            description: Optional[str], defaults to random if empty
            datasource_type: DataSourceType enum member
            shared: If True, enable 'Shared with project' toggle
            integration: Optionally select integration string

        Returns:
            The name used for the datasource
        """
        name = name or get_random_name()
        description = description or get_random_name()
        self.fill_name(name)
        self.fill_description(description)
        if project_name:
            self.selector.search_and_select_project(project_name)
        self.select_datasource_type(datasource_type)
        if shared:
            self.toggle_shared_with_project()
        if integration:
            self.select_integration(integration)
        return name

    @step
    def create_git_datasource(
        self,
        name: Optional[str] = None,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        shared: bool = False,
        repo_link: Optional[str] = None,
        branch: Optional[str] = None,
        summarization_method: Optional[str] = None,
        embeddings_model: Optional[str] = None,
        integration: Optional[str] = None,
    ):
        """
        Creates a Git DataSource with required and optional fields.
        """
        name = self._base_create_datasource(
            name, project_name, description, DataSourceType.GIT, shared, integration
        )
        if repo_link:
            self.fill_repo_link(repo_link)
        if branch:
            self.fill_branch(branch)
        if summarization_method:
            self.select_summarization_method(summarization_method)
        if embeddings_model:
            self.select_embeddings_model(embeddings_model)
        self.click_create()
        return name

    @step
    def create_confluence_datasource(
        self,
        name: Optional[str] = None,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        shared: bool = False,
        cql_query: Optional[str] = None,
        integration: Optional[str] = None,
    ):
        """
        Creates a Confluence DataSource with required and optional fields.
        """
        name = self._base_create_datasource(
            name,
            project_name,
            description,
            DataSourceType.CONFLUENCE,
            shared,
            integration,
        )
        if cql_query:
            self.fill_cql_query(cql_query)
        self.click_create()
        return name

    @step
    def create_jira_datasource(
        self,
        name: Optional[str] = None,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        shared: bool = False,
        jql_query: Optional[str] = None,
        integration: Optional[str] = None,
    ):
        """
        Creates a Jira DataSource with required and optional fields.
        """
        name = self._base_create_datasource(
            name, project_name, description, DataSourceType.JIRA, shared, integration
        )
        if jql_query:
            self.fill_jql_query(jql_query)
        self.click_create()
        return name

    @step
    def create_file_datasource(
        self,
        name: Optional[str] = None,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        shared: bool = False,
        file_path: Optional[str] = None,
        integration: Optional[str] = None,
    ):
        """
        Creates a File DataSource with required and optional fields.
        """
        name = self._base_create_datasource(
            name, project_name, description, DataSourceType.FILE, shared, integration
        )
        if file_path:
            self.select_file(file_path)
        self.click_create()
        return name

    @step
    def create_google_datasource(
        self,
        name: Optional[str] = None,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        shared: bool = False,
        google_doc_link: Optional[str] = None,
        integration: Optional[str] = None,
    ):
        """
        Creates a Google DataSource with required and optional fields.
        """
        name = self._base_create_datasource(
            name, project_name, description, DataSourceType.GOOGLE, shared, integration
        )
        if google_doc_link:
            self.fill_google_doc_link(google_doc_link)
        self.click_create()
        return name

    # -------------------------------
    # Git DataSource Type Methods
    # -------------------------------

    @step
    def select_summarization_method(self, value: str):
        self.summarization_method_dropdown.click()
        self.dropdown_values(value).click()
        return self

    @step
    def fill_repo_link(self, value: str):
        self.repo_link_input.fill(value)
        return self

    @step
    def fill_branch(self, value: str):
        self.branch_input.fill(value)
        return self

    @step
    def fill_files_filter(self, value: str):
        self.files_filter_input.fill(value)
        return self

    @step
    def select_embeddings_model(self, value: str):
        self.embeddings_model_dropdown.click()
        self.dropdown_values(value).click()
        return self

    # -------------------------------
    # Confluence DataSource Type Methods
    # -------------------------------

    @step
    def fill_cql_query(self, cql: str):
        self.cql_query_input.fill(cql)
        return self

    # -------------------------------
    # Jira DataSource Type Methods
    # -------------------------------

    @step
    def fill_jql_query(self, jql: str):
        self.jql_query_input.fill(jql)
        return self

    # -------------------------------
    # File DataSource Type Methods
    # -------------------------------

    @step
    def select_file(self, path: str):
        self.input_file.set_input_files(path)
        return self

    @step
    def add_file(self):
        self.add_file_button.click()
        return self

    # -------------------------------
    # Google DataSource Type Methods
    # -------------------------------

    @step
    def fill_google_doc_link(self, link: str):
        self.google_query_input.fill(link)
        return self

    # -----------------
    # Verification Methods
    # -----------------

    @step
    def should_see_name_input(self):
        expect(self.name_input).to_be_visible()
        return self

    @step
    def should_see_disabled_name_input(self, name: str):
        expect(self.disabled_name_input).to_be_visible()
        expect(self.disabled_name_input).to_have_value(name)
        return self

    @step
    def should_see_description_input(self):
        expect(self.description_input).to_be_visible()
        return self

    @step
    def should_see_shared_with_project_switch(self):
        expect(self.shared_with_project_switch).to_be_visible()
        return self

    @step
    def should_see_datasource_type_input(self):
        expect(self.datasource_type_selector).to_be_visible()
        # default value is Git
        expect(self.datasource_type_selector).to_have_value("Git")
        return self

    @step
    def should_see_datasource_type_dropdown_values(self):
        self.datasource_type_dropdown.click()
        for type in DATA_SOURCE_TYPES_LIST:
            expect(self.dropdown_values(type)).to_be_visible()

    @step
    def should_see_create_button(self):
        expect(self.create_button).to_be_visible()
        return self

    @step
    def should_see_cancel_button(self):
        expect(self.cancel_button).to_be_visible()
        return self

    @step
    def should_see_save_reindex_button(self):
        expect(self.save_reindex_button).to_be_visible()
        return self

    @step
    def should_see_integration_input(self):
        expect(self.integration_input).to_be_visible()
        return self

    @step
    def should_see_add_integration_button(self):
        expect(self.add_integration_button).to_be_visible()
        return self

    @step
    def should_see_integration_input_or_button(self):
        """
        Verifies that either the integration input OR the add integration button is visible.
        """
        try:
            self.should_see_integration_input()
        except AssertionError:
            self.should_see_add_integration_button()
        return self

    @step
    def should_see_selected_integration(self, integration: str):
        expect(self.integration_input).to_have_text(integration)
        return self

    @step
    def should_see_main_fields(self):
        self.should_see_name_input()
        self.should_see_description_input()
        self.selector.should_see_multiselect()
        self.should_see_shared_with_project_switch()
        self.should_see_datasource_type_input()
        self.should_see_create_button()
        self.should_see_cancel_button()
        self.should_see_datasource_type_dropdown_values()
        return self

    @step
    def should_see_error_for_empty_main_fields(self):
        expect(self.error_name_input).to_be_visible()
        expect(self.error_name_input).to_have_text(EMPTY_NAME_ERROR)
        expect(self.error_description_input).to_be_visible()
        expect(self.error_description_input).to_have_text(EMPTY_DESCRIPTION_ERROR)
        return self

    @step
    def should_see_error_for_empty_git_fields(self):
        expect(self.error_repo_link_input).to_be_visible()
        expect(self.error_repo_link_input).to_have_text(EMPTY_REPO_LINK_ERROR)
        expect(self.error_branch_input).to_be_visible()
        expect(self.error_branch_input).to_have_text(EMPTY_BRANCH_ERROR)
        return self

    @step
    def should_see_error_for_empty_confluence_fields(self):
        expect(self.error_cql_query_input).to_be_visible()
        expect(self.error_cql_query_input).to_have_text(EMPTY_CQL_ERROR)
        return self

    @step
    def should_see_error_for_empty_jira_fields(self):
        expect(self.error_jql_query_input).to_be_visible()
        expect(self.error_jql_query_input).to_have_text(EMPTY_JQL_ERROR)
        return self

    @step
    def should_see_error_for_empty_file_fields(self):
        expect(self.error_files_info_text).to_be_visible()
        expect(self.error_files_info_text).to_have_text(EMPTY_FILE_ERROR)
        return self

    @step
    def should_see_error_for_empty_google_fields(self):
        expect(self.error_google_query_input).to_be_visible()
        expect(self.error_google_query_input).to_have_text(EMPTY_GOOGLE_LINK_ERROR)
        return self

    # -------------------------------
    # Git DataSource Type Verification Methods
    # -------------------------------

    @step
    def should_see_summarization_fields(self):
        expect(self.summarization_method_input).to_be_visible()
        expect(self.summarization_method_dropdown).to_be_visible()
        return self

    @step
    def should_see_summarization_dropdown_values(self):
        self.summarization_method_dropdown.click()
        for method in SUMMARIZATION_METHODS_LIST:
            expect(self.dropdown_values(method)).to_be_visible()

    @step
    def should_see_repo_fields(self):
        expect(self.repo_link_input).to_be_visible()
        expect(self.branch_input).to_be_visible()
        return self

    @step
    def should_see_files_filter_textarea(self):
        expect(self.files_filter_input).to_be_visible()
        return self

    @step
    def should_see_embeddings_model_field(self):
        expect(self.embeddings_model_input).to_be_visible()
        expect(self.embeddings_model_dropdown).to_be_visible()
        return self

    @step
    def should_see_embeddings_model_dropdown_values(self):
        self.embeddings_model_dropdown.click()
        for model in EMBEDDING_MODELS_LIST:
            expect(self.dropdown_values(model)).to_be_visible()
        self.page.click("body")
        return self

    @step
    def should_see_git_fields(self):
        self.should_see_summarization_fields()
        self.should_see_embeddings_model_dropdown_values()
        self.should_see_repo_fields()
        self.should_see_files_filter_textarea()
        self.should_see_embeddings_model_field()
        self.should_see_embeddings_model_dropdown_values()
        self.should_see_integration_input_or_button()
        return self

    # -------------------------------
    # Confluence DataSource Type Verification Methods
    # -------------------------------

    @step
    def should_see_confluence_cql_field(self):
        expect(self.cql_query_input).to_be_visible()
        return self

    # -------------------------------
    # Jira DataSource Type Verification Methods
    # -------------------------------

    @step
    def should_see_jira_jql_field(self):
        expect(self.jql_query_input).to_be_visible()
        return self

    # -------------------------------
    # File DataSource Type Verification Methods
    # -------------------------------

    @step
    def should_see_file_fields(self):
        expect(self.select_file_button).to_be_visible()
        expect(self.add_file_button).to_be_visible()
        expect(self.files_info_text).to_be_visible()
        expect(self.files_info_text).to_have_text(FILE_INSTRUCTIONS)
        return self

    @step
    def should_see_uploaded_file(self, file_name: str):
        expect(self.file_input_field).to_be_visible()
        expect(self.file_input_field).to_have_text(file_name)
        return self

    @step
    def should_see_csv_config(self):
        expect(self.csv_separator_input).to_be_visible()
        expect(self.csv_separator_input).to_have_value("; (selmicolor)")
        expect(self.csv_separator_dropdown_button).to_be_visible()
        expect(self.csv_start_row_input).to_be_visible()
        expect(self.csv_start_row_input).to_have_text("1")
        expect(self.csv_rows_per_document_input).to_be_visible()
        expect(self.csv_rows_per_document_input).to_have_value("1")
        return self

    # -------------------------------
    # Google DataSource Type Verification Methods
    # -------------------------------

    @step
    def should_see_google_fields(self):
        expect(self.google_query_input).to_be_visible()
        expect(self.google_instructions.nth(0)).to_be_visible()
        expect(self.google_instructions.nth(1)).to_be_visible()
        expect(self.google_instructions.nth(0)).to_have_text(GOOGLE_INSTRUCTIONS)
        expect(self.google_instructions.nth(0).locator("a")).to_have_attribute(
            "href", GOOGLE_GUIDE_URL
        )
        expect(self.google_instructions.nth(1)).to_have_text(GOOGLE_EXAMPLE)
        expect(self.google_instructions.nth(1).locator("a")).to_have_attribute(
            "href", GOOGLE_DOC_URL
        )
        return self
