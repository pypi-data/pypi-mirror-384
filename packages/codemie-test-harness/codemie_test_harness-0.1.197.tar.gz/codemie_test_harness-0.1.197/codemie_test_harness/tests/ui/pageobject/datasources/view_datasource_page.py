#
from codemie_test_harness.tests.ui.pageobject.base_page import BasePage
from hamcrest import greater_than_or_equal_to, assert_that
from playwright.sync_api import expect
from reportportal_client import step
from codemie_test_harness.tests.ui.pageobject.datasources.datasource_sidebar import (
    DataSourceSidebar,
)


class ViewDatasourcePage(BasePage):
    """
    Page object for the 'View DataSource' details page.
    Contains all major section locators and verification methods (with text checks).
    """

    def __init__(self, page):
        self.sidebar = DataSourceSidebar(page)
        self.page = page

    # Main Page Elements
    @property
    def back_button(self):
        return self.page.locator("div.h-layout-header button").first

    @property
    def main_title(self):
        return self.page.locator("h1.text-h3.text-white.font-semibold")

    # Name/Owner/Shared
    @property
    def datasource_name(self):
        return self.page.locator("h4.text-2xl.font-semibold.font-mono")

    @property
    def owner_text(self):
        return self.page.locator("div.flex.gap-4.text-xs.text-text-secondary p").first

    @property
    def shared_status(self):
        return self.page.locator(
            "span.text-xs.text-switch-label, span.flex.items-center.gap-1"
        )

    # Overview Section
    @property
    def overview_label(self):
        return self.page.locator(
            "p.text-xs.text-text-main.font-semibold", has_text="OVERVIEW"
        )

    @property
    def project_value(self):
        return self.page.locator("div.gap-x-3 p:text('Project:') + p")

    @property
    def datasource_type_value(self):
        return self.page.locator("div.gap-x-3 p:text('Data Source Type:') + p")

    @property
    def datasource_id_field(self):
        return self.page.locator(
            "div.flex.flex-col.gap-2.mt-2.uppercase input[readonly]"
        )

    # Description
    @property
    def description_label(self):
        return self.page.locator("h5.font-bold.text-xs.mb-2", has_text="Description")

    @property
    def description_text(self):
        return self.description_label.locator("xpath=../div")

    # Configuration Section
    @property
    def configuration_label(self):
        return self.page.locator(
            "p.text-xs.text-text-main.font-semibold", has_text="CONFIGURATION"
        )

    @property
    def embeddings_model_label(self):
        return self.page.locator(
            "p.text-xs.text-text-tertiary", has_text="Embeddings model:"
        )

    @property
    def embeddings_model_value(self):
        return self.embeddings_model_label.locator("+ div")

    @property
    def summarization_model_label(self):
        return self.page.locator(
            "p.text-xs.text-text-tertiary", has_text="Summarization model:"
        )

    @property
    def summarization_model_value(self):
        return self.summarization_model_label.locator("+ div")

    # Usage Details Section
    @property
    def usage_label(self):
        return self.page.locator(
            "p.text-xs.text-text-main.font-semibold", has_text="USAGE DETAILS"
        )

    @property
    def input_tokens_label(self):
        return self.page.locator(
            "p.text-xs.text-text-tertiary", has_text="Input tokens used:"
        )

    @property
    def input_tokens_value(self):
        return self.input_tokens_label.locator("xpath=../div")

    @property
    def output_tokens_label(self):
        return self.page.locator(
            "p.text-xs.text-text-tertiary", has_text="Output tokens used:"
        )

    @property
    def output_tokens_value(self):
        return self.output_tokens_label.locator("xpath=../div")

    @property
    def money_spent_label(self):
        return self.page.locator(
            "p.text-xs.text-text-tertiary", has_text="Money spent:"
        )

    @property
    def money_spent_value(self):
        return self.money_spent_label.locator("xpath=../div")

    # Processing Summary
    @property
    def processing_summary_label(self):
        return self.page.locator(
            "h5.font-bold.text-xs.leading-none.font-mono", has_text="Processing Summary"
        )

    @property
    def total_documents_label(self):
        return self.page.locator(
            "div.font-mono.text-ds-field-title", has_text="Total documents:"
        )

    @property
    def total_documents_count(self):
        return self.total_documents_label.locator("xpath=../span")

    @property
    def processed_documents_label(self):
        return self.page.locator(
            "div.font-mono.text-ds-field-title", has_text="Processed Documents Count:"
        )

    @property
    def processed_documents_count(self):
        return self.processed_documents_label.locator("xpath=../span")

    @property
    def imported_chunks_label(self):
        return self.page.locator(
            "div.font-mono.text-ds-field-title", has_text="Imported Chunks Count:"
        )

    @property
    def imported_chunks_count(self):
        return self.imported_chunks_label.locator("xpath=../span")

    @property
    def skipped_documents_label(self):
        return self.page.locator(
            "div.font-mono.text-ds-field-title", has_text="Skipped Documents:"
        )

    @property
    def skipped_documents_count(self):
        return self.skipped_documents_label.locator("xpath=../span")

    @property
    def total_size_kb_label(self):
        return self.page.locator(
            "div.font-mono.text-ds-field-title", has_text="Total Size KB:"
        )

    @property
    def total_size_kb_count(self):
        return self.total_size_kb_label.locator("xpath=../span")

    @property
    def average_file_size_b_label(self):
        return self.page.locator(
            "div.font-mono.text-ds-field-title", has_text="Average File Size B:"
        )

    @property
    def average_file_size_b_count(self):
        return self.average_file_size_b_label.locator("xpath=../span")

    # Processed Data
    @property
    def processed_data_tab_label(self):
        return self.page.locator("ul li a.p-menuitem-link", has_text="Processed Data")

    @property
    def processed_data_label(self):
        return self.page.locator("h5.text-xs", has_text="Processed Data")

    @property
    def processed_data_list(self):
        return self.page.locator("ul.bg-new-panel li")

    # --- Verification Methods ---

    @step
    def should_see_title_and_back_button(self):
        expect(self.main_title).to_have_text("Data Source Details")
        expect(self.back_button).to_be_visible()
        return self

    @step
    def should_see_ds_name_and_owner(
        self, datasource_name: str = None, owner: str = None
    ):
        expect(self.datasource_name).to_be_visible()
        if datasource_name:
            expect(self.datasource_name).to_have_text(datasource_name)
        expect(self.owner_text).to_be_visible()
        if owner:
            expect(self.owner_text).to_have_text(f"by {owner}")
        return self

    @step
    def should_see_overview(
        self, project: str = None, ds_type: str = None, ds_id: str = None
    ):
        expect(self.overview_label).to_be_visible()
        expect(self.project_value).to_be_visible()
        if project:
            expect(self.project_value).to_have_text(project)
        expect(self.datasource_type_value).to_be_visible()
        if ds_type:
            expect(self.datasource_type_value).to_have_text(ds_type)
        expect(self.datasource_id_field).to_be_visible()
        if ds_id:
            expect(self.datasource_id_field).to_have_value(ds_id)
        return self

    @step
    def should_see_description(self, description: str = None):
        expect(self.description_label).to_be_visible()
        expect(self.description_text).to_be_visible()
        if description:
            expect(self.description_text).to_have_text(description)
        return self

    @step
    def should_see_configuration(
        self, embeddings_model: str = None, summarization_model: str = None
    ):
        expect(self.configuration_label).to_be_visible()
        expect(self.embeddings_model_label).to_be_visible()
        expect(self.embeddings_model_value).to_be_visible()
        if embeddings_model:
            expect(self.embeddings_model_value).to_have_text(embeddings_model)
        expect(self.summarization_model_label).to_be_visible()
        expect(self.summarization_model_value).to_be_visible()
        if summarization_model:
            expect(self.summarization_model_value).to_have_text(summarization_model)
        return self

    @step
    def should_see_usage_details(self):
        expect(self.usage_label).to_be_visible()
        expect(self.input_tokens_label).to_be_visible()
        expect(self.input_tokens_value).to_be_visible()
        expect(self.output_tokens_label).to_be_visible()
        expect(self.output_tokens_value).to_be_visible()
        expect(self.money_spent_label).to_be_visible()
        expect(self.money_spent_value).to_be_visible()
        return self

    @step
    def should_see_processing_summary(
        self,
        total_documents: str = None,
        processed_documents: str = None,
        imported_chunks: str = None,
        skipped_documents: str = None,
        is_git: bool = False,
    ):
        expect(self.processing_summary_label).to_be_visible()
        expect(self.total_documents_label).to_be_visible()
        expect(self.total_documents_count).to_be_visible()
        if total_documents:
            expect(self.total_documents_count).to_have_text(total_documents)
        expect(self.processed_documents_label).to_be_visible()
        expect(self.processed_documents_count).to_be_visible()
        if processed_documents:
            expect(self.processed_documents_count).to_have_text(processed_documents)
        expect(self.imported_chunks_label).to_be_visible()
        expect(self.imported_chunks_count).to_be_visible()
        if imported_chunks:
            expect(self.imported_chunks_count).to_have_text(imported_chunks)
        expect(self.skipped_documents_label).to_be_visible()
        expect(self.skipped_documents_count).to_be_visible()
        if skipped_documents:
            expect(self.skipped_documents_count).to_have_text(skipped_documents)
        if is_git:
            expect(self.total_size_kb_label).to_be_visible()
            expect(self.total_documents_count).to_be_visible()
            expect(self.average_file_size_b_label).to_be_visible()
            expect(self.average_file_size_b_count).to_be_visible()
        return self

    @step
    def should_open_and_see_processed_data(self, min_count: int = 1):
        expect(self.processed_data_tab_label).to_be_visible()
        self.processed_data_tab_label.click()
        expect(self.processed_data_list.first).to_be_visible()
        count = self.processed_data_list.count()
        assert_that(count, greater_than_or_equal_to(min_count))
        return self

    @step
    def should_see_processed_data(self, min_count: int = 1):
        expect(self.processed_data_label).to_be_visible()
        expect(self.processed_data_list.first).to_be_visible()
        count = self.processed_data_list.count()
        assert_that(count, greater_than_or_equal_to(min_count))
        return self
