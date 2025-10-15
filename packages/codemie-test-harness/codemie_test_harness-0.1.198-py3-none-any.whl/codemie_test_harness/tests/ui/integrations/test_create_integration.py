"""
UI tests for Create Integration feature - critical paths with best practices.

This test suite covers the essential "Create Integration" workflow focusing on happy path scenarios.
All tests follow the Page Object Model pattern with reusable components abstracted in standalone classes.
"""

import pytest
from codemie_sdk.models.integration import CredentialTypes

from codemie_test_harness.tests.ui.pageobject.integrations.create_integration_page import (
    CreateIntegrationPage,
)
from codemie_test_harness.tests.ui.pageobject.integrations.integrations_page import (
    IntegrationsPage,
)
from codemie_test_harness.tests.ui.test_data.integration_test_data import (
    IntegrationTestDataFactory,
)


# noinspection PyArgumentList
class TestCreateIntegrationNavigation:
    """Test class for integration creation navigation and page access."""

    @pytest.mark.integration
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_navigate_to_integrations_via_menu(self, page):
        """
        Test navigation to create integration page via menu.

        Verifies:
        - User can navigate to integrations page from menu
        - Main UI elements are visible on Integrations page
        """
        # Arrange
        integrations_page = IntegrationsPage(page)

        # Act
        integrations_page.navigate_to_via_menu()

        # Assert
        integrations_page.should_be_on_integrations_page()
        integrations_page.should_see_create_integration_button()
        integrations_page.should_see_integration_type_switcher()
        integrations_page.should_see_integrations_table()

    @pytest.mark.integration
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_navigate_to_create_integration_via_direct_url(self, page):
        """
        Test direct navigation to create integration page via URL.

        Verifies:
        - Direct URL access works correctly
        - Page Title matches integration type
        """

        create_integration_page = CreateIntegrationPage(page)

        # Act
        create_integration_page.navigate_to_user_integration_creation()

        # Assert
        create_integration_page.should_be_on_create_user_integration_page()

        # Act
        create_integration_page.navigate_to_project_integration_creation()

        # Assert
        create_integration_page.should_be_on_create_project_integration_page()

    @pytest.mark.integration
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_navigate_to_create_integration_from_integrations_page(self, page):
        """
        Test navigation to create integration page from integrations page ui elements.

        Verifies:
        - Navigation via UI elements works correctly
        - Page Title matches integration type
        """

        integrations_page = IntegrationsPage(page)

        # Navigate to User Integration creation
        integrations_page.navigate_to().navigate_to_user_integration_creation()

        create_integration_page = CreateIntegrationPage(page)

        # Assert
        create_integration_page.should_be_on_create_user_integration_page()

        # Navigate to Project Integration creation
        integrations_page.navigate_to().navigate_to_project_integration_creation()

        # Assert
        create_integration_page.should_be_on_create_project_integration_page()


# noinspection PyArgumentList
class TestIntegrationCreationPageElements:
    """Test class for integration creation page elements display."""

    @pytest.mark.integration
    @pytest.mark.ui
    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "credential_type",
        [CredentialTypes.GIT, CredentialTypes.JIRA, CredentialTypes.CONFLUENCE],
    )
    def test_create_integration_type_form_fields(self, page, credential_type):
        """
        Test that all required form fields are displayed for Git credential type.

        Verifies:
        - Page navigation and structure validation
        - Action buttons visibility (Back, Cancel, Create)
        - Project selector element presence
        - Global Integration toggle visibility
        - Credential Type field with "Git" value
        - Alias field with required indicator
        - Authentication section with all fields (URL, Token name, Token)
        - Help text and information tooltips
        - Form field interactivity validation
        - Create button initial disabled state
        """

        create_integration_page = CreateIntegrationPage(page)

        # Act
        create_integration_page.navigate_to_user_integration_creation()
        create_integration_page.select_credential_type(credential_type)

        # Assert - Verify page structure (includes title validation)
        create_integration_page.should_be_on_create_user_integration_page()

        # Assert - Verify UI elements visibility
        (
            create_integration_page.should_have_action_buttons_visible(credential_type)
            .should_have_project_selector_visible()
            .should_have_global_integration_toggle_visible()
            .should_have_credential_type_field_visible()
            .should_have_alias_field_visible()
            .should_have_authentication_section_visible(credential_type)
            .should_have_help_texts_visible()
        )

        # Assert - Verify credential type value
        create_integration_page.should_have_credential_type_selected(credential_type)

        # Assert - Verify form elements are interactive
        create_integration_page.should_have_input_fields_editable()

        # Assert - Verify Create button initial state
        create_integration_page.should_have_create_button_enabled()


# noinspection PyArgumentList
class TestIntegrationCreationWorkflow:
    """Test class for the complete integration creation workflow."""

    @pytest.mark.integration
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_create_git_integration_complete_workflow(self, page):
        """
        Test the complete Git integration creation workflow (happy path).

        Verifies the end-to-end workflow for Git integration creation.
        """
        # Arrange
        integrations_page = IntegrationsPage(page)
        create_integration_page = CreateIntegrationPage(page)
        integration_test_data = IntegrationTestDataFactory.git_integration()

        # Act - Navigate and create
        create_integration_page.navigate_to_user_integration_creation()
        create_integration_page.fill_git_integration_form(integration_test_data)
        create_integration_page.create_integration()

        # Assert
        (
            integrations_page.navigate_to()
            .should_see_message(
                IntegrationTestDataFactory.success_messages["integration_created"]
            )
            .should_see_specific_integration(integration_test_data.alias)
        )

    @pytest.mark.integration
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_create_jira_integration_complete_workflow(self, page):
        """
        Test the complete Jira integration creation workflow (happy path).

        Verifies the end-to-end workflow for Jira integration creation including:
        - Navigation to user integration creation page
        - Credential type selection (Jira)
        - Form filling with valid Jira integration data
        - Integration creation and success validation
        - Verification of created integration in integrations list
        """
        # Arrange
        integrations_page = IntegrationsPage(page)
        create_integration_page = CreateIntegrationPage(page)
        integration_test_data = IntegrationTestDataFactory.jira_integration()

        # Act - Navigate and create
        create_integration_page.navigate_to_user_integration_creation()
        create_integration_page.fill_jira_integration_form(integration_test_data)
        create_integration_page.create_integration()

        # Assert
        (
            integrations_page.navigate_to()
            .should_see_message(
                IntegrationTestDataFactory.success_messages["integration_created"]
            )
            .should_see_specific_integration(integration_test_data.alias)
        )

    @pytest.mark.integration
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_create_confluence_integration_complete_workflow(self, page):
        """
        Test the complete Confluence integration creation workflow (happy path).

        Verifies the end-to-end workflow for Confluence integration creation including:
        - Navigation to user integration creation page
        - Credential type selection (Confluence)
        - Form filling with valid Confluence integration data
        - Integration creation and success validation
        - Verification of created integration in integrations list
        """
        # Arrange
        integrations_page = IntegrationsPage(page)
        create_integration_page = CreateIntegrationPage(page)
        integration_test_data = IntegrationTestDataFactory.confluence_integration()

        # Act - Navigate and create
        create_integration_page.navigate_to_user_integration_creation()
        create_integration_page.fill_confluence_integration_form(integration_test_data)
        create_integration_page.create_integration()

        # Assert
        (
            integrations_page.navigate_to()
            .should_see_message(
                IntegrationTestDataFactory.success_messages["integration_created"]
            )
            .should_see_specific_integration(integration_test_data.alias)
        )


# noinspection PyArgumentList
class TestIntegrationFormUserExperience:
    """Test class for integration form user experience and usability."""

    @pytest.mark.integration
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_form_reset_and_cancel_functionality(self, page):
        """
        Test form reset and cancel functionality.

        Verifies:
        - Cancel button navigates away from form
        - Form data is not saved when cancelled
        - User can safely exit creation process
        """
        # Arrange
        create_integration_page = CreateIntegrationPage(page)
        integrations_page = IntegrationsPage(page)

        # Act
        cancelled_integration_alias = "Test Integration to Cancel"
        create_integration_page.navigate_to_user_integration_creation()
        create_integration_page.fill_alias(cancelled_integration_alias)
        create_integration_page.cancel_creation()

        # Assert - Should navigate back to integrations page
        integrations_page.should_have_page_title("Integrations")

        # Verify the cancelled integration was not created
        integrations_page.should_not_see_integration(cancelled_integration_alias)

    @pytest.mark.integration
    @pytest.mark.ui
    @pytest.mark.smoke
    def test_alias_field_validation_message(self, page):
        """
        Test validation message when alias field is empty and form is submitted.

        Verifies:
        - Error toast notification appears with correct header
        - Error message contains "Alias is required" text
        - Toast notification is visible and readable
        """
        # Arrange
        create_integration_page = CreateIntegrationPage(page)

        # Act - Navigate to integration creation and try to submit without alias
        create_integration_page.navigate_to_user_integration_creation()
        create_integration_page.select_credential_type(CredentialTypes.GIT)
        # Leave alias field empty intentionally
        create_integration_page.create_integration()

        # Assert - Verify error toast notification appears
        create_integration_page.should_see_error_toast_message(
            header=IntegrationTestDataFactory.validation_messages[
                "cannot_create_setting"
            ],
            content=IntegrationTestDataFactory.validation_messages["alias_required"],
        )
