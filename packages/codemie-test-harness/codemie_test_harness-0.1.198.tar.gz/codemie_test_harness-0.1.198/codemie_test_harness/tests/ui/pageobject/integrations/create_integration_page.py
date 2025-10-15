"""
Create Integration page object for the integration creation workflow.
Contains methods for filling out integration forms, selecting types, and completing the creation process.
"""

from codemie_sdk.models.integration import CredentialTypes
from playwright.sync_api import expect, Locator
from reportportal_client import step

from codemie_test_harness.tests.ui.pageobject.base_page import BasePage
from codemie_test_harness.tests.ui.test_data.integration_test_data import (
    IntegrationTestData,
)


# noinspection PyArgumentList
class CreateIntegrationPage(BasePage):
    """Create Integration page with comprehensive form handling and validation."""

    def __init__(self, page):
        super().__init__(page)

    # Header elements
    @property
    def page_title(self) -> Locator:
        """Page title element showing 'New User Integration'."""
        return self.page.locator(".text-h3.font-semibold")

    @property
    def create_button(self) -> Locator:
        """Create button to save the integration."""
        return self.page.locator('button.button.primary.medium[role="submit"]').filter(
            has_text="Create"
        )

    @property
    def test_button(self) -> Locator:
        """Test button to test the integration."""
        return self.page.locator("button.button.secondary.medium").filter(
            has_text="Test"
        )

    # Form container
    @property
    def form_container(self) -> Locator:
        """Main form container."""
        return self.page.locator("form.flex.flex-col.gap-y-6")

    # Project selection
    @property
    def project_selector(self) -> Locator:
        """Project multiselect dropdown."""
        return self.page.locator('#projectSelector[data-pc-name="multiselect"]')

    @property
    def project_selector_label(self) -> Locator:
        """Project selector label container."""
        return self.project_selector.locator(".p-multiselect-label")

    @property
    def project_selector_trigger(self) -> Locator:
        """Project selector dropdown trigger button."""
        return self.project_selector.locator(".p-multiselect-trigger")

    @property
    def project_search_input(self) -> Locator:
        """Project selector lookup."""
        return self.page.locator(
            'input[role="searchbox"][placeholder="Search for projects"]'
        )

    # Global Integration toggle
    @property
    def global_integration_checkbox(self) -> Locator:
        """Global Integration checkbox input."""
        return self.page.locator('input#isGlobal[name="is_global"]')

    @property
    def global_integration_switch(self) -> Locator:
        """Global Integration switch wrapper."""
        return self.page.locator("label.switch-wrapper#isGlobal")

    # Cloud toggle
    @property
    def is_cloud_checkbox(self) -> Locator:
        """Cloud checkbox input."""
        return self.page.locator("input#isCloud")

    @property
    def is_cloud_switch(self) -> Locator:
        """Cloud switch wrapper."""
        return self.page.locator("label.switch-wrapper#isCloud")

    # Credential Type selection
    @property
    def credential_type_input(self) -> Locator:
        """Credential Type autocomplete input field."""
        return self.page.locator("#credentialType input.p-autocomplete-input")

    @property
    def credential_type_dropdown_button(self) -> Locator:
        """Credential Type dropdown button."""
        return self.page.locator("#credentialType button.p-autocomplete-dropdown")

    # Alias field (required)
    @property
    def alias_input(self) -> Locator:
        """Integration alias input field (required)."""
        return self.page.locator('input#settingAlias[data-testid="validation"]')

    @property
    def alias_label(self) -> Locator:
        """Alias field label."""
        return self.page.locator('label[for="settingAlias"] .input-label')

    @property
    def alias_required_indicator(self) -> Locator:
        """Required indicator for alias field."""
        return self.alias_label.locator(".input-label-required")

    # Authentication section
    @property
    def authentication_heading(self) -> Locator:
        """Authentication section heading."""
        return self.page.locator('h4:has-text("Authentication")')

    @property
    def url_input(self) -> Locator:
        """URL input field in authentication section."""
        return self.page.locator('input#url[data-testid="validation"]')

    @property
    def token_name_input(self) -> Locator:
        """Token name input field."""
        return self.page.locator('input#name[data-testid="validation"]')

    @property
    def token_input(self) -> Locator:
        """Token input field."""
        return self.page.locator('input#token[data-testid="validation"]')

    @property
    def user_name_input(self) -> Locator:
        """User Name input."""
        return self.page.locator("input#username")

    # Information tooltips and help text
    @property
    def global_integration_help_text(self) -> Locator:
        """Information text explaining global integration feature."""
        return self.page.locator(".text-text-secondary.text-xs").filter(
            has_text="By enabling, it will become versatile"
        )

    @property
    def authentication_help_text(self) -> Locator:
        """Security information text about masked sensitive data."""
        return self.page.locator(".text-text-secondary.text-xs").filter(
            has_text="Important note: Your sensitive information is encrypted for security"
        )

    # Validation elements
    @property
    def validation_errors(self) -> Locator:
        """All validation error messages on the page."""
        return self.page.locator(".error-message, .validation-error, .field-error")

    # Toast notification elements
    @property
    def error_toast_header(self) -> Locator:
        """Error toast notification header."""
        return self.page.locator(".codemie-toast-err .codemie-toast-header")

    @property
    def error_toast_content(self) -> Locator:
        """Error toast notification content message."""
        return self.page.locator(".codemie-toast-err .codemie-toast-content")

    # Navigation methods
    @step
    def navigate_to_user_integration_creation(self):
        """Navigate to the create user integration page."""
        self.page.goto("/#/integrations/user/new")
        self.wait_for_page_load()
        return self

    @step
    def navigate_to_project_integration_creation(self):
        """Navigate to the create project integration page."""
        self.page.goto("/#/integrations/project/new")
        self.wait_for_page_load()
        return self

    @step
    def go_back(self):
        """Click the back button to return to previous page."""
        self.back_button.click()
        return self

    # Project selection methods
    @step
    def open_project_selector(self):
        """Open the project selector dropdown."""
        self.project_selector_trigger.click()
        return self

    @step
    def select_project(self, project_name: str):
        """
        Select a project from the dropdown.

        Args:
            project_name (str): Name of the project to select
        """
        self.open_project_selector()
        self.project_search_input.fill(project_name)
        project_option = self.page.locator(
            f'[data-pc-section="item"]:has-text("{project_name}")'
        )
        if project_option.is_visible():
            project_option.click()
        else:
            # If exact match not found, press Enter to accept typed value
            self.project_search_input.press("Enter")
        return self

    @step
    def get_selected_project(self) -> str:
        """
        Get the currently selected project name.

        Returns:
            str: Currently selected project name
        """
        return self.project_selector_label.text_content().strip()

    # Global Integration methods
    @step
    def enable_global_integration(self):
        """Enable the Global Integration toggle."""
        if not self.global_integration_checkbox.is_checked():
            self.global_integration_switch.click()
        return self

    @step
    def disable_global_integration(self):
        """Disable the Global Integration toggle."""
        if self.global_integration_checkbox.is_checked():
            self.global_integration_switch.click()
        return self

    @step
    def is_global_integration_enabled(self) -> bool:
        """
        Check if Global Integration is enabled.

        Returns:
            bool: True if enabled, False otherwise
        """
        return self.global_integration_checkbox.is_checked()

    # Credential Type methods
    @step
    def select_credential_type(self, credential_type: CredentialTypes):
        """
        Select a credential type from the autocomplete dropdown.

        Args:
            credential_type: Type of credential to select (e.g., 'Git', 'AWS', etc.)
        """
        # Clear current selection and type new value
        self.credential_type_input.clear()
        self.credential_type_input.fill(credential_type.value)

        # Wait for dropdown options to appear and select the matching option
        option = self.page.locator(
            f'li[role="option"][aria-label="{credential_type.value}"]'
        )
        if option.is_visible():
            option.click()
        else:
            # If exact match not found, press Enter to accept typed value
            self.credential_type_input.press("Enter")
        return self

    @step
    def get_credential_type(self) -> str:
        """
        Get the currently selected credential type.

        Returns:
            str: Currently selected credential type
        """
        return self.credential_type_input.input_value()

    # Form filling methods
    @step
    def fill_alias(self, alias: str):
        """
        Fill the integration alias field.

        Args:
            alias (str): Integration alias name
        """
        self.alias_input.clear()
        self.alias_input.fill(alias)
        return self

    @step
    def fill_url(self, url: str):
        """
        Fill the URL field in authentication section.

        Args:
            url (str): URL value
        """
        self.url_input.clear()
        self.url_input.fill(url)
        return self

    @step
    def fill_token_name(self, token_name: str):
        """
        Fill the token name field.

        Args:
            token_name (str): Token name value
        """
        self.token_name_input.clear()
        self.token_name_input.fill(token_name)
        return self

    @step
    def fill_token(self, token: str):
        """
        Fill the token field.

        Args:
            token (str): Token value
        """
        self.token_input.clear()
        self.token_input.fill(token)
        return self

    @step
    def fill_username(self, username: str):
        """
        Fill the username field.

        Args:
            username (str): Username value
        """
        self.user_name_input.clear()
        self.user_name_input.fill(username)
        return self

    # Cloud mode methods
    @step
    def enable_cloud_mode(self):
        """Enable the Cloud mode toggle."""
        if not self.is_cloud_checkbox.is_checked():
            self.is_cloud_switch.click()
        return self

    @step
    def disable_cloud_mode(self):
        """Disable the Cloud mode toggle."""
        if self.is_cloud_checkbox.is_checked():
            self.is_cloud_switch.click()
        return self

    @step
    def is_cloud_mode_enabled(self) -> bool:
        """
        Check if Cloud mode is enabled.

        Returns:
            bool: True if enabled, False otherwise
        """
        return self.is_cloud_checkbox.is_checked()

    @step
    def fill_git_integration_form(self, test_data: IntegrationTestData):
        """
        Fill the complete Git integration form with provided data.

        Args:
            test_data: IntegrationTestData
        """
        # Fill project
        self.select_project(test_data.project)

        # Fill required alias field
        self.fill_alias(test_data.alias)

        # Select credential type
        self.select_credential_type(test_data.credential_type)

        # Set global integration if requested
        if test_data.is_global:
            self.enable_global_integration()
        else:
            self.disable_global_integration()

        # Fill authentication fields
        self.fill_url(test_data.fields["url"])
        self.fill_token(test_data.fields["token"])

        return self

    @step
    def fill_jira_integration_form(self, test_data: IntegrationTestData):
        """
        Fill the complete Jira integration form with provided data.

        Args:
            test_data: IntegrationTestData containing Jira-specific fields
        """
        # Fill project
        self.select_project(test_data.project)

        # Fill required alias field
        self.fill_alias(test_data.alias)

        # Select credential type
        self.select_credential_type(test_data.credential_type)

        # Set global integration if requested
        if test_data.is_global:
            self.enable_global_integration()
        else:
            self.disable_global_integration()

        # Fill authentication fields specific to Jira
        self.fill_url(test_data.fields["url"])

        # Set cloud mode if specified
        if test_data.fields.get("is_cloud", False):
            self.enable_cloud_mode()
            self.fill_username(test_data.fields["username"])
        else:
            self.disable_cloud_mode()

        self.fill_token(test_data.fields["token"])

        return self

    @step
    def fill_confluence_integration_form(self, test_data: IntegrationTestData):
        """
        Fill the complete Confluence integration form with provided data.

        Args:
            test_data: IntegrationTestData containing Confluence-specific fields
        """
        # Fill project
        self.select_project(test_data.project)

        # Fill required alias field
        self.fill_alias(test_data.alias)

        # Select credential type
        self.select_credential_type(test_data.credential_type)

        # Set global integration if requested
        if test_data.is_global:
            self.enable_global_integration()
        else:
            self.disable_global_integration()

        # Fill authentication fields specific to Confluence
        self.fill_url(test_data.fields["url"])

        # Set cloud mode if specified
        if test_data.fields.get("is_cloud", False):
            self.enable_cloud_mode()
            self.fill_username(test_data.fields["username"])
        else:
            self.disable_cloud_mode()

        self.fill_token(test_data.fields["token"])

        return self

    # Action methods
    @step
    def create_integration(self):
        """Click the Create button to save the integration."""
        self.create_button.click()
        return self

    @step
    def cancel_creation(self):
        """Click the Cancel button to exit without saving."""
        self.cancel_button.click()
        return self

    # Helper methods
    @step
    def wait_for_form_to_load(self):
        """Wait for the form to fully load with all elements visible."""
        expect(self.form_container).to_be_visible()
        expect(self.alias_input).to_be_visible()
        expect(self.create_button).to_be_visible()
        return self

    @step
    def get_form_data(self) -> dict:
        """
        Get current form data as a dictionary.

        Returns:
            dict: Current form field values
        """
        return {
            "project": self.get_selected_project(),
            "credential_type": self.get_credential_type(),
            "alias": self.alias_input.input_value(),
            "url": self.url_input.input_value(),
            "token_name": self.token_name_input.input_value(),
            "token": self.token_input.input_value(),
            "is_global": self.is_global_integration_enabled(),
        }

    @step
    def clear_all_fields(self):
        """Clear all form fields."""
        self.alias_input.clear()
        self.url_input.clear()
        self.token_name_input.clear()
        self.token_input.clear()
        self.credential_type_input.clear()
        self.disable_global_integration()
        return self

    # ==================== VERIFICATION METHODS ====================

    @step
    def should_have_action_buttons_visible(
        self, credential_type: CredentialTypes
    ) -> "CreateIntegrationPage":
        """
        Verify that all action buttons (back, cancel, test, create) are visible.

        Returns:
            self: For method chaining
        """
        #
        expect(self.back_button).to_be_visible()
        expect(self.cancel_button).to_be_visible()
        expect(self.create_button).to_be_visible()
        if credential_type in [CredentialTypes.JIRA, CredentialTypes.CONFLUENCE]:
            expect(self.test_button).to_be_visible()
        else:
            expect(self.test_button).not_to_be_visible()
        return self

    @step
    def should_have_project_selector_visible(self) -> "CreateIntegrationPage":
        """
        Verify that project selector and its label are visible.

        Returns:
            self: For method chaining
        """
        expect(self.project_selector).to_be_visible()
        expect(self.project_selector_label).to_be_visible()
        return self

    @step
    def should_have_global_integration_toggle_visible(self) -> "CreateIntegrationPage":
        """
        Verify that global integration toggle elements are visible.

        Returns:
            self: For method chaining
        """
        expect(self.global_integration_switch).to_be_visible()
        return self

    @step
    def should_have_credential_type_field_visible(self) -> "CreateIntegrationPage":
        """
        Verify that credential type field elements are visible.

        Returns:
            self: For method chaining
        """
        expect(self.credential_type_input).to_be_visible()
        expect(self.credential_type_dropdown_button).to_be_visible()
        return self

    @step
    def should_have_alias_field_visible(self) -> "CreateIntegrationPage":
        """
        Verify that alias field and required indicator are visible.

        Returns:
            self: For method chaining
        """
        expect(self.alias_input).to_be_visible()
        expect(self.alias_required_indicator).to_be_visible()
        return self

    # Mapping of credential types to their specific fields
    def credential_based_fields(self):
        return {
            CredentialTypes.GIT: [
                self.url_input,
                self.token_name_input,
                self.token_input,
            ],
            CredentialTypes.JIRA: [
                self.url_input,
                self.user_name_input,
                self.is_cloud_switch,
                self.token_input,
            ],
            CredentialTypes.CONFLUENCE: [
                self.url_input,
                self.user_name_input,
                self.is_cloud_switch,
                self.token_input,
            ],
        }

    @step
    def should_have_authentication_section_visible(
        self, credentials_type: CredentialTypes
    ) -> "CreateIntegrationPage":
        """
        Verify that authentication section heading and fields are visible.

        Returns:
            self: For method chaining
        """
        expect(self.authentication_heading).to_be_visible()
        for element in self.credential_based_fields()[credentials_type]:
            expect(element).to_be_visible()
        return self

    @step
    def should_have_help_texts_visible(self) -> "CreateIntegrationPage":
        """
        Verify that help texts and information tooltips are visible.

        Returns:
            self: For method chaining
        """
        expect(self.global_integration_help_text).to_be_visible()
        (
            expect(self.global_integration_help_text).to_have_text(
                "By enabling, it will become versatile and can be applied across multiple projects without being tied to any specific one."
            )
        )
        expect(self.authentication_help_text).to_be_visible()
        (
            expect(self.authentication_help_text).to_have_text(
                "Important note: Your sensitive information is encrypted for security and displayed here in a masked format. If you're updating non-sensitive information, there's no need to modify the masked values — they will remain unchanged and secure."
            )
        )
        return self

    def should_have_input_fields_editable(self) -> "CreateIntegrationPage":
        expect(self.alias_input).to_be_editable()
        if self.url_input.is_visible():
            expect(self.url_input).to_be_editable()
        if self.token_name_input.is_visible():
            expect(self.token_name_input).to_be_editable()
        if self.token_input.is_visible():
            expect(self.token_input).to_be_editable()
        return self

    @step
    def should_be_on_create_user_integration_page(self):
        """Verify that the user is on the create user integration page."""
        expect(self.page).to_have_url("/#/integrations/user/new")
        expect(self.page_title).to_have_text("New User Integration")
        return self

    @step
    def should_be_on_create_project_integration_page(self):
        """Verify that the user is on the create project integration page."""
        expect(self.page).to_have_url("/#/integrations/project/new")
        expect(self.page_title).to_have_text("New Project Integration")
        return self

    @step
    def should_have_create_button_enabled(self):
        """Verify that the create button is enabled."""
        expect(self.create_button).to_be_enabled()
        return self

    @step
    def should_have_create_button_disabled(self):
        """Verify that the create button is disabled."""
        expect(self.create_button).to_be_disabled()
        return self

    @step
    def should_see_validation_error(self, field_name: str, error_message: str):
        """
        Verify that a specific validation error is displayed for a field.

        Args:
            field_name (str): Name of the field with error
            error_message (str): Expected error message
        """
        error_locator = self.page.locator(
            f'[data-testid="validation-error-{field_name}"]'
        )
        if not error_locator.is_visible():
            # Fallback to generic error message locator
            error_locator = self.validation_errors.filter(has_text=error_message)
        expect(error_locator).to_be_visible()
        expect(error_locator).to_contain_text(error_message)
        return self

    @step
    def should_not_see_validation_errors(self):
        """Verify that no validation errors are displayed."""
        expect(self.validation_errors).to_have_count(0)
        return self

    @step
    def should_have_project_selected(self, project_name: str):
        """
        Verify that a specific project is selected.

        Args:
            project_name (str): Expected selected project name
        """
        expect(self.project_selector_label).to_have_text(project_name)
        return self

    @step
    def should_have_credential_type_selected(self, credential_type: CredentialTypes):
        """
        Verify that a specific credential type is selected.

        Args:
            credential_type: Expected credential type
        """
        expect(self.credential_type_input).to_have_value(credential_type.value)
        return self

    @step
    def should_have_global_integration_enabled(self):
        """Verify that global integration toggle is enabled."""
        expect(self.global_integration_checkbox).to_be_checked()
        return self

    @step
    def should_have_global_integration_disabled(self):
        """Verify that global integration toggle is disabled."""
        expect(self.global_integration_checkbox).not_to_be_checked()
        return self

    @step
    def should_see_error_toast_message(self, header: str, content: str):
        """
        Verify that error toast notification is displayed with expected header and content.

        Args:
            header (str): Expected toast header text
            content (str): Expected toast content message
        """
        expect(self.error_toast_header).to_be_visible()
        expect(self.error_toast_header).to_have_text(header)
        expect(self.error_toast_content).to_be_visible()
        expect(self.error_toast_content).to_contain_text(content)
        return self
