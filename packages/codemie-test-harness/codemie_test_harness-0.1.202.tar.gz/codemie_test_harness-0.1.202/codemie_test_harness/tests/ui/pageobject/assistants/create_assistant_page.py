from typing import Optional

from playwright.sync_api import expect, Locator
from reportportal_client import step

from codemie_test_harness.tests.ui.pageobject.assistants.generate_with_ai_modal import (
    AIAssistantGeneratorPage,
)
from codemie_test_harness.tests.ui.pageobject.base_page import BasePage


class CreateAssistantPage(BasePage):
    """
    Create Assistant page object following Page Object Model (POM) best practices.

    This class encapsulates all interactions with the Create Assistant page,
    providing a clean interface for test automation while hiding implementation details.
    Updated with accurate locators based on real HTML structure.
    """

    page_url = "/#/assistants/new"

    def __init__(self, page):
        """Initialize the Create Assistant page object."""
        super().__init__(page)
        self.ai_generator_modal = AIAssistantGeneratorPage(
            page
        )  # AI Assistant Generator modal

    # =============================================================================
    # LOCATORS - Core Page Elements
    # =============================================================================

    @property
    def main_container(self) -> Locator:
        """Main page container"""
        return self.page.locator("main.flex.flex-col.h-full.flex-1")

    @property
    def page_title(self) -> Locator:
        """Page title 'Create Assistant' element"""
        return (
            self.page.locator('.text-h3:has-text("Create Assistant")')
            or self.page.locator(
                'div.text-h3.text-white.font-semibold:has-text("Create Assistant")'
            )
            or self.page.locator('h1:has-text("Create Assistant")')
        )

    @property
    def generate_with_ai_button(self) -> Locator:
        """Generate with AI button in header with magical styling"""
        return (
            self.page.locator(
                'button.button.magical.medium:has-text("Generate with AI")'
            )
            or self.page.locator('button:has-text("Generate with AI")')
            or self.page.locator("button:has(svg + text)").filter(
                has_text="Generate with AI"
            )
        )

    @property
    def create_button(self) -> Locator:
        """Create button with plus icon (primary button)"""
        return (
            self.page.locator("button#submit")
            or self.page.locator('button.button.primary.medium:has-text("Create")')
            or self.page.locator('button:has-text("Create"):has(svg)')
        )

    # =============================================================================
    # LOCATORS - Assistant Setup Section
    # =============================================================================

    @property
    def assistant_setup_section(self) -> Locator:
        """Assistant Setup section header"""
        return self.page.locator('h4:has-text("Assistant Setup")')

    @property
    def project_dropdown(self) -> Locator:
        """Project selection multiselect dropdown"""
        return (
            self.page.locator("div.p-multiselect#project")
            or self.page.locator('[name="project"].p-multiselect')
            or self.page.locator(".p-multiselect-label-container")
        )

    @property
    def shared_toggle(self) -> Locator:
        """'Shared with project' toggle switch"""
        return self.page.locator("label.switch-wrapper span.switch")

    @property
    def name_input(self) -> Locator:
        """Assistant name input field with data-testid validation"""
        return (
            self.page.locator('input#name[data-testid="validation"]')
            or self.page.locator('input[placeholder="Name*"]')
            or self.page.locator('input[name="name"]')
        )

    @property
    def slug_input(self) -> Locator:
        """Assistant slug input field"""
        return (
            self.page.locator('input#slug[data-testid="validation"]')
            or self.page.locator(
                'input[placeholder="Unique human-readable identifier"]'
            )
            or self.page.locator('input[name="slug"]')
        )

    @property
    def icon_url_input(self) -> Locator:
        """Assistant icon URL input field"""
        return (
            self.page.locator('input#icon_url[data-testid="validation"]')
            or self.page.locator('input[placeholder="URL to the assistant\'s icon"]')
            or self.page.locator('input[name="icon_url"]')
        )

    @property
    def description_textarea(self) -> Locator:
        """Assistant description textarea with placeholder"""
        return (
            self.page.locator('textarea#description[name="description"]')
            or self.page.locator('textarea[placeholder="Description*"]')
            or self.page.locator(".textarea-wrapper textarea")
        )

    @property
    def conversation_starters_input(self) -> Locator:
        """Conversation starters input field with InputGroup"""
        return (
            self.page.locator("input.p-inputtext#conversationStarters-0")
            or self.page.locator('input[name="conversationStarters"]')
            or self.page.locator(".p-inputgroup input")
        )

    @property
    def add_conversation_starter_button(self) -> Locator:
        """Add conversation starter button with plus icon"""
        return (
            self.page.locator('button.button.secondary.medium:has-text("Add")').nth(0)
            or self.page.locator('button:has-text("Add"):has(svg)').first
            or self.page.locator('.flex.justify-between button:has-text("Add")')
        )

    @property
    def delete_conversation_starter_button(self) -> Locator:
        """Delete conversation starter button (trash icon in InputGroup)"""
        return (
            self.page.locator(".p-inputgroup-addon button:has(svg)")
            or self.page.locator('button:has(path[d*="M9.5 1.25a3.25"])')
            or self.page.locator(".p-inputgroup button")
        )

    # =============================================================================
    # LOCATORS - Behavior & Logic Section
    # =============================================================================

    @property
    def behavior_logic_section(self) -> Locator:
        """Behavior & Logic section header"""
        return self.page.locator('h4:has-text("Behavior & Logic")')

    @property
    def system_instructions_label(self) -> Locator:
        """System Instructions label"""
        return self.page.locator(
            '.text-sm.font-semibold:has-text("System Instructions")'
        )

    @property
    def system_prompt_textarea(self) -> Locator:
        """System instructions textarea with full height"""
        return (
            self.page.locator('textarea#system_prompt[name="system_prompt"]')
            or self.page.locator('textarea[placeholder="System Instructions*"]')
            or self.page.locator(".textarea-wrapper.h-full textarea")
        )

    @property
    def expand_system_prompt_button(self) -> Locator:
        """Expand system prompt button"""
        return (
            self.page.locator('button.button.secondary.medium:has-text("Expand")')
            or self.page.locator('button:has-text("Expand"):has(svg)')
            or self.page.locator('.flex.gap-4 button:has-text("Expand")')
        )

    @property
    def model_type_dropdown(self) -> Locator:
        """LLM model type multiselect dropdown"""
        return (
            self.page.locator("div.p-multiselect#model_type")
            or self.page.locator('[name="model_type"].p-multiselect')
            or self.page.locator(
                '.p-multiselect:has(.p-multiselect-label:has-text("Default LLM Model"))'
            )
        )

    @property
    def temperature_input(self) -> Locator:
        """Temperature input field (0-2 range)"""
        return (
            self.page.locator('input#temperature[data-testid="validation"]')
            or self.page.locator('input[placeholder="0-2"]')
            or self.page.locator('input[name="temperature"]')
        )

    @property
    def top_p_input(self) -> Locator:
        """Top P input field (0-1 range)"""
        return (
            self.page.locator('input#top_p[data-testid="validation"]')
            or self.page.locator('input[placeholder="0-1"]')
            or self.page.locator('input[name="top_p"]')
        )

    # ==================== NAVIGATION METHODS ====================

    @step
    def navigate_to(self):
        """
        Navigate to the Create Assistant page.

        Returns:
            self: Returns the page object for method chaining
        """
        self.page.goto(self.page_url)
        self.wait_for_page_load()

        # Handle AI Generator modal if it appears
        self.handle_ai_generator_modal_if_visible()

        return self

    # ==================== AI GENERATOR MODAL METHODS ====================

    @step
    def is_ai_generator_modal_visible(self) -> bool:
        """
        Check if the AI Assistant Generator modal is currently visible.

        Returns:
            bool: True if modal is visible, False otherwise
        """
        return self.ai_generator_modal.is_modal_visible()

    @step
    def close_ai_generator_modal(self):
        """
        Close the AI Assistant Generator modal if it's visible.

        Returns:
            self: Returns the page object for method chaining
        """
        if self.is_ai_generator_modal_visible():
            self.ai_generator_modal.close_modal()
        return self

    @step
    def handle_ai_generator_modal_if_visible(self):
        """
        Handle the AI Generator modal if it appears when navigating to Create Assistant page.
        This method will close the modal to proceed with manual assistant creation.

        Returns:
            self: Returns the page object for method chaining
        """
        # Wait a short moment for modal to potentially appear
        self.page.wait_for_timeout(1000)

        if self.is_ai_generator_modal_visible():
            # Modal is visible, close it to proceed with manual creation
            self.close_ai_generator_modal()

            # Wait for modal to fully disappear before proceeding
            self.page.wait_for_timeout(500)

        return self

    @step
    def verify_ai_generator_modal_visible(self):
        """
        Verify that the AI Assistant Generator modal is visible with correct structure.

        Returns:
            self: Returns the page object for method chaining
        """
        assert self.is_ai_generator_modal_visible(), (
            "AI Assistant Generator modal should be visible"
        )

        # Verify modal structure using updated methods
        self.ai_generator_modal.verify_modal_title()
        self.ai_generator_modal.verify_description_text()
        self.ai_generator_modal.verify_prompt_label()
        self.ai_generator_modal.verify_note_text()

        return self

    @step
    def verify_ai_generator_modal_not_visible(self):
        """
        Verify that the AI Assistant Generator modal is not visible.

        Returns:
            self: Returns the page object for method chaining
        """
        assert not self.is_ai_generator_modal_visible(), (
            "AI Assistant Generator modal should not be visible"
        )
        return self

    @step
    def create_manually_from_ai_modal(self):
        """
        Click 'Create Manually' from the AI Generator modal to proceed with manual creation.

        Returns:
            self: Returns the page object for method chaining
        """
        if self.is_ai_generator_modal_visible():
            self.ai_generator_modal.click_create_manually()
            # Wait for the modal to close and manual form to appear
            self.page.wait_for_timeout(1000)
        return self

    @step
    def generate_with_ai_from_modal(
        self,
        description: str,
        include_tools: bool = True,
        do_not_show_again: bool = False,
    ):
        """
        Use the AI Generator modal to create an assistant with AI.

        Args:
            description: Description of the assistant to generate
            include_tools: Whether to include tools in the assistant
            do_not_show_again: Whether to check 'do not show popup' option

        Returns:
            self: Returns the page object for method chaining
        """
        if self.is_ai_generator_modal_visible():
            self.ai_generator_modal.complete_ai_generation_workflow(
                prompt=description,
                include_tools=include_tools,
                dont_show_again=do_not_show_again,
            )
        return self

    # ==================== FORM INTERACTION METHODS ====================

    @step
    def fill_name(self, name: str):
        """
        Fill the assistant name field.

        Args:
            name: The name for the assistant

        Returns:
            self: Returns the page object for method chaining
        """
        self.name_input.clear()
        self.name_input.fill(name)
        return self

    @step
    def fill_description(self, description: str):
        """
        Fill the assistant description field.

        Args:
            description: The description for the assistant

        Returns:
            self: Returns the page object for method chaining
        """
        self.description_textarea.clear()
        self.description_textarea.fill(description)
        return self

    @step
    def fill_system_prompt(self, prompt: str):
        """
        Fill the system prompt field.

        Args:
            prompt: The system prompt text

        Returns:
            self: Returns the page object for method chaining
        """
        self.system_prompt_textarea.clear()
        self.system_prompt_textarea.fill(prompt)
        return self

    @step
    def fill_icon_url(self, icon_url: str):
        """
        Fill the icon URL field.

        Args:
            icon_url: The URL for the assistant icon

        Returns:
            self: Returns the page object for method chaining
        """
        self.icon_url_input.clear()
        self.icon_url_input.fill(icon_url)
        return self

    @step
    def fill_slug(self, slug: str):
        """
        Fill the slug field.

        Args:
            slug: The unique identifier for the assistant

        Returns:
            self: Returns the page object for method chaining
        """
        self.slug_input.clear()
        self.slug_input.fill(slug)
        return self

    @step
    def toggle_shared_assistant(self, shared: bool = True):
        """
        Toggle the shared/public setting for the assistant.

        Args:
            shared: Whether the assistant should be shared (True) or private (False)

        Returns:
            self: Returns the page object for method chaining
        """
        # Check current state and toggle if needed
        is_currently_checked = self.shared_toggle.is_checked()
        if (shared and not is_currently_checked) or (
            not shared and is_currently_checked
        ):
            self.shared_toggle.click()
        return self

    @step
    def fill_temperature(self, temperature: str):
        """
        Fill the temperature field.

        Args:
            temperature: Temperature value (0-2)

        Returns:
            self: Returns the page object for method chaining
        """
        self.temperature_input.clear()
        self.temperature_input.fill(temperature)
        return self

    @step
    def fill_top_p(self, top_p: str):
        """
        Fill the Top P field.

        Args:
            top_p: Top P value (0-1)

        Returns:
            self: Returns the page object for method chaining
        """
        self.top_p_input.clear()
        self.top_p_input.fill(top_p)
        return self

    # ==================== ACTION METHODS ====================

    @step
    def click_create(self):
        """
        Click the Create button to create the assistant.

        Returns:
            self: Returns the page object for method chaining
        """
        self.create_button.click()
        return self

    @step
    def click_cancel(self):
        """
        Click the Cancel button to abort assistant creation.

        Returns:
            self: Returns the page object for method chaining
        """
        self.cancel_button.click()
        return self

    @step
    def click_back(self):
        """
        Click the Back button to return to assistants list.

        Returns:
            self: Returns the page object for method chaining
        """
        self.back_button.click()
        return self

    @step
    def click_generate_with_ai_header(self):
        """
        Click the Generate with AI button in the header.

        Returns:
            self: Returns the page object for method chaining
        """
        self.generate_with_ai_button.click()
        return self

    # ==================== COMPREHENSIVE ASSISTANT CREATION METHOD ====================

    @step
    def create_assistant(
        self,
        name: str,
        description: str,
        system_prompt: str,
        icon_url: Optional[str] = None,
        shared: bool = False,
        temperature: Optional[str] = None,
        top_p: Optional[str] = None,
    ):
        """
        Complete assistant creation workflow with all required parameters.

        This method encapsulates the entire assistant creation process,
        following the critical happy path scenario outlined in the requirements.

        Args:
            name: Assistant name (required)
            description: Assistant description (required)
            system_prompt: System prompt for the assistant (required)
            slug: Optional unique identifier for the assistant
            icon_url: Optional icon URL for the assistant
            shared: Whether to make the assistant shared/public (default: False)
            temperature: Optional temperature value (0-2)
            top_p: Optional Top P value (0-1)

        Returns:
            self: Returns the page object for method chaining
        """
        # Fill essential required fields
        self.fill_name(name)
        self.fill_description(description)
        self.fill_system_prompt(system_prompt)

        # Fill optional fields if provided
        # if icon_url:
        #     self.fill_icon_url(icon_url)
        # if temperature:
        #     self.fill_temperature(temperature)
        # if top_p:
        #     self.fill_top_p(top_p)

        # Set sharing preference
        self.toggle_shared_assistant(shared)

        # Submit the form
        self.click_create()

        return self

    # ==================== VERIFICATION METHODS ====================

    @step
    def should_be_on_create_assistant_page(self):
        """Verify that we are on the Create Assistant page."""
        expect(self.page_title).to_be_visible()
        expect(self.page).to_have_url(f"{self.page_url}")
        return self

    @step
    def should_have_all_form_fields_visible(self):
        """Verify that all essential form fields are visible."""
        expect(self.name_input).to_be_visible()
        expect(self.description_textarea).to_be_visible()
        expect(self.system_prompt_textarea).to_be_visible()
        return self

    @step
    def should_have_action_buttons_visible(self):
        """Verify that action buttons (Create, Cancel) are visible."""
        expect(self.create_button).to_be_visible()
        expect(self.cancel_button).to_be_visible()
        return self

    @step
    def should_have_name_value(self, expected_name: str):
        """Verify name field has expected value."""
        expect(self.name_input).to_have_value(expected_name)
        return self

    @step
    def should_have_description_value(self, expected_description: str):
        """Verify description field has expected value."""
        expect(self.description_textarea).to_have_value(expected_description)
        return self

    @step
    def should_have_system_prompt_value(self, expected_prompt: str):
        """Verify system prompt field has expected value."""
        expect(self.system_prompt_textarea).to_have_value(expected_prompt)
        return self

    @step
    def should_have_icon_url_value(self, expected_url: str):
        """Verify icon URL field has expected value."""
        expect(self.icon_url_input).to_have_value(expected_url)
        return self

    @step
    def should_have_shared_checked(self):
        """Verify shared toggle is checked."""
        expect(self.shared_toggle).to_be_checked()
        return self

    @step
    def should_have_shared_unchecked(self):
        """Verify shared toggle is unchecked."""
        expect(self.shared_toggle).not_to_be_checked()
        return self

    @step
    def should_have_create_button_enabled(self):
        """Verify create button is enabled."""
        expect(self.create_button).to_be_enabled()
        return self

    @step
    def should_have_create_button_disabled(self):
        """Verify create button is disabled."""
        expect(self.create_button).to_be_disabled()
        return self

    @step
    def should_have_cancel_button_enabled(self):
        """Verify cancel button is enabled."""
        expect(self.cancel_button).to_be_enabled()
        return self

    @step
    def should_have_empty_fields(self):
        """Verify all form fields are empty."""
        expect(self.name_input).to_have_value("")
        expect(self.description_textarea).to_have_value("")
        expect(self.system_prompt_textarea).to_have_value("")
        expect(self.icon_url_input).to_have_value("")
        return self
