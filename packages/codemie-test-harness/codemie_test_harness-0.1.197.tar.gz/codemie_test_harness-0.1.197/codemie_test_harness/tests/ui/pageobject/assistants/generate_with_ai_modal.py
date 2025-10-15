import logging

from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)


class AIAssistantGeneratorPage:
    """
    Page Object Model for the Generate Assistant with AI form.

    This form allows users to create AI assistants by describing their requirements
    and configuring various options including tool integrations.
    """

    def __init__(self, page: Page):
        """
        Initialize the AI Assistant Generator page object.

        Args:
            page: Playwright page instance
        """
        self.page = page
        self._setup_locators()

    def _setup_locators(self) -> None:
        """Define all locators for the AI Assistant Generator form based on actual HTML structure."""

        # Modal container
        self.modal_container = self.page.locator(".popup").filter(
            has_text="Generate Assistant with AI"
        )

        # Header elements
        self.modal_header = self.modal_container.locator(".popup-header.withBorder")
        self.modal_title = self.modal_header.locator("h4")
        self.close_button = self.modal_header.locator(
            'button[aria-label="Close popup"]'
        )

        # Modal body
        self.modal_body = self.modal_container.locator(".popup-body")

        # Description elements - Updated based on actual structure
        self.description_text = self.modal_body.locator("p").first
        self.assistant_description_label = self.modal_body.locator("p").nth(1)

        # Main textarea - Updated with actual name attribute
        self.assistant_description_textarea = (
            self.modal_body.locator('textarea[name="ai_generation_prompt"]')
            .or_(self.modal_body.locator(".textarea-wrapper textarea"))
            .or_(self.modal_body.locator("textarea.textarea"))
        )

        # Checkbox elements - Updated with actual IDs
        self.do_not_show_checkbox = (
            self.modal_body.locator('input#dont_show[type="checkbox"]')
            .or_(self.modal_body.locator('input[name="dont_show"]'))
            .or_(self.modal_body.locator('.p-checkbox input[type="checkbox"]'))
        )
        self.do_not_show_label = self.modal_body.locator('label[for="dont_show"]')

        # Include tools toggle - Updated with actual ID
        self.include_tools_toggle = (
            self.modal_body.locator('input#include_tools[type="checkbox"]')
            .or_(self.modal_body.locator('input[name="include_tools"]'))
            .or_(self.modal_body.locator('.switch-wrapper input[type="checkbox"]'))
        )
        self.include_tools_label = self.modal_body.locator(".switch-wrapper .label")

        # Action buttons - Updated based on actual button classes
        self.create_manually_button = (
            self.modal_body.locator(
                'button.button.secondary:has-text("Create Manualy")'
            )
            .or_(self.modal_body.locator('button:has-text("Create Manualy")'))
            .or_(self.modal_body.locator(".button.secondary"))
        )
        self.generate_with_ai_button = (
            self.modal_body.locator(
                'button.button.primary:has-text("Generate with AI")'
            )
            .or_(self.modal_body.locator('button:has-text("Generate with AI")'))
            .or_(self.modal_body.locator(".button.primary"))
        )

        # Note text - Updated based on actual structure
        self.integration_note = self.modal_body.locator(".text-text-secondary.text-xs")
        self.info_icon = self.modal_body.locator(".flex.w-full.px-2 svg").first

    # Navigation and state methods

    def wait_for_modal_to_load(self, timeout: float = 10000) -> None:
        """
        Wait for the AI Assistant Generator modal to be fully loaded and visible.

        Args:
            timeout: Maximum time to wait in milliseconds
        """
        logger.info("Waiting for AI Assistant Generator modal to load")
        expect(self.modal_container).to_be_visible(timeout=timeout)
        expect(self.modal_title).to_be_visible()
        expect(self.assistant_description_textarea).to_be_visible()
        logger.info("AI Assistant Generator modal loaded successfully")

    def is_modal_visible(self) -> bool:
        """
        Check if the AI Assistant Generator modal is currently visible.

        Returns:
            True if modal is visible, False otherwise
        """
        return self.modal_container.is_visible()

    def close_modal(self) -> None:
        """Close the AI Assistant Generator modal using the close button."""
        logger.info("Closing AI Assistant Generator modal")
        self.close_button.click()
        expect(self.modal_container).not_to_be_visible()
        logger.info("AI Assistant Generator modal closed successfully")

    # Form interaction methods

    def enter_assistant_description(self, description: str) -> None:
        """
        Enter description text in the assistant description textarea.

        Args:
            description: The assistant description text to enter
        """
        logger.info(f"Entering assistant description: {description[:50]}...")
        self.assistant_description_textarea.click()
        self.assistant_description_textarea.clear()
        self.assistant_description_textarea.fill(description)

        # Verify the text was entered correctly
        expect(self.assistant_description_textarea).to_have_value(description)
        logger.info("Assistant description entered successfully")

    def get_assistant_description(self) -> str:
        """
        Get the current value of the assistant description textarea.

        Returns:
            Current text value in the description textarea
        """
        return self.assistant_description_textarea.input_value()

    def toggle_do_not_show_popup(self, enabled: bool = True) -> None:
        """
        Toggle the "Do not show this popup" checkbox.

        Args:
            enabled: True to check the checkbox, False to uncheck
        """
        logger.info(f"Setting 'Do not show popup' to: {enabled}")

        if enabled and not self.do_not_show_checkbox.is_checked():
            self.do_not_show_checkbox.check()
        elif not enabled and self.do_not_show_checkbox.is_checked():
            self.do_not_show_checkbox.uncheck()

        # Verify the state
        if enabled:
            expect(self.do_not_show_checkbox).to_be_checked()
        else:
            expect(self.do_not_show_checkbox).not_to_be_checked()

        logger.info(f"'Do not show popup' checkbox set to: {enabled}")

    def is_do_not_show_popup_checked(self) -> bool:
        """
        Check if the "Do not show this popup" checkbox is checked.

        Returns:
            True if checkbox is checked, False otherwise
        """
        return self.do_not_show_checkbox.is_checked()

    def toggle_include_tools(self, enabled: bool = True) -> None:
        """
        Toggle the "Include Tools" option.

        Args:
            enabled: True to enable tools inclusion, False to disable
        """
        logger.info(f"Setting 'Include Tools' to: {enabled}")

        if enabled and not self.include_tools_toggle.is_checked():
            self.include_tools_toggle.check()
        elif not enabled and self.include_tools_toggle.is_checked():
            self.include_tools_toggle.uncheck()

        # Verify the state
        if enabled:
            expect(self.include_tools_toggle).to_be_checked()
        else:
            expect(self.include_tools_toggle).not_to_be_checked()

        logger.info(f"'Include Tools' toggle set to: {enabled}")

    def is_include_tools_enabled(self) -> bool:
        """
        Check if the "Include Tools" toggle is enabled.

        Returns:
            True if toggle is enabled, False otherwise
        """
        return self.include_tools_toggle.is_checked()

    # Action methods

    def click_create_manually(self) -> None:
        """Click the 'Create Manually' button."""
        logger.info("Clicking 'Create Manually' button")
        expect(self.create_manually_button).to_be_enabled()
        self.create_manually_button.click()
        logger.info("'Create Manually' button clicked")

    def click_generate_with_ai(self) -> None:
        """Click the 'Generate with AI' button."""
        logger.info("Clicking 'Generate with AI' button")
        expect(self.generate_with_ai_button).to_be_enabled()
        self.generate_with_ai_button.click()
        logger.info("'Generate with AI' button clicked")

    # Validation methods

    def is_generate_button_enabled(self) -> bool:
        """
        Check if the 'Generate with AI' button is enabled.

        Returns:
            True if button is enabled, False otherwise
        """
        return self.generate_with_ai_button.is_enabled()

    def is_create_manually_button_enabled(self) -> bool:
        """
        Check if the 'Create Manually' button is enabled.

        Returns:
            True if button is enabled, False otherwise
        """
        return self.create_manually_button.is_enabled()

    def validate_form_elements_visible(self) -> None:
        """Validate that all expected form elements are visible and accessible."""
        logger.info("Validating AI Assistant Generator form elements visibility")

        # Check modal structure
        expect(self.modal_container).to_be_visible()
        expect(self.modal_title).to_be_visible()
        expect(self.close_button).to_be_visible()

        # Check form elements
        expect(self.assistant_description_label).to_be_visible()
        expect(self.assistant_description_textarea).to_be_visible()
        expect(self.do_not_show_label).to_be_visible()
        expect(self.do_not_show_checkbox).to_be_visible()
        expect(self.include_tools_label).to_be_visible()
        expect(self.include_tools_toggle).to_be_visible()

        # Check action buttons
        expect(self.create_manually_button).to_be_visible()
        expect(self.generate_with_ai_button).to_be_visible()

        # Check note text
        expect(self.integration_note).to_be_visible()

        logger.info("All form elements are visible and accessible")

    def validate_textarea_placeholder(self) -> None:
        """Validate that the textarea has the expected placeholder text."""
        placeholder_text = self.assistant_description_textarea.get_attribute(
            "placeholder"
        )
        expected_text = "For example: I need a project assistant that helps track deadlines, work with Jira and help with business requirements"

        assert expected_text in placeholder_text, (
            f"Placeholder text mismatch. Expected: {expected_text}, Got: {placeholder_text}"
        )
        logger.info("Textarea placeholder validation passed")

    def verify_modal_title(self) -> None:
        """Verify the modal has the correct title."""
        expect(self.modal_title).to_have_text("Generate Assistant with AI")
        logger.info("Modal title verification passed")

    def verify_description_text(self) -> None:
        """Verify the main description text is present."""
        expect(self.description_text).to_contain_text("Describe your ideal assistant")
        logger.info("Description text verification passed")

    def verify_prompt_label(self) -> None:
        """Verify the prompt question is displayed."""
        expect(self.assistant_description_label).to_have_text(
            "What should your assistant do?"
        )
        logger.info("Prompt label verification passed")

    def verify_note_text(self) -> None:
        """Verify the note about tool integrations."""
        expect(self.integration_note).to_contain_text(
            "Note: Please select tool integrations after generation"
        )
        logger.info("Note text verification passed")

    # Composite action methods

    def fill_and_generate_assistant(
        self,
        description: str,
        include_tools: bool = True,
        do_not_show_again: bool = False,
    ) -> None:
        """
        Complete workflow to fill the form and generate an AI assistant.

        Args:
            description: Assistant description text
            include_tools: Whether to include tools in the assistant
            do_not_show_again: Whether to check "do not show popup" option
        """
        logger.info("Starting complete assistant generation workflow")

        # Wait for modal to be ready
        self.wait_for_modal_to_load()

        # Fill form fields
        self.enter_assistant_description(description)
        self.toggle_include_tools(include_tools)
        self.toggle_do_not_show_popup(do_not_show_again)

        # Generate the assistant
        self.click_generate_with_ai()

        logger.info("Assistant generation workflow completed")

    def fill_and_create_manually(
        self,
        description: str,
        include_tools: bool = True,
        do_not_show_again: bool = False,
    ) -> None:
        """
        Complete workflow to fill the form and create assistant manually.

        Args:
            description: Assistant description text
            include_tools: Whether to include tools in the assistant
            do_not_show_again: Whether to check "do not show popup" option
        """
        logger.info("Starting manual assistant creation workflow")

        # Wait for modal to be ready
        self.wait_for_modal_to_load()

        # Fill form fields
        self.enter_assistant_description(description)
        self.toggle_include_tools(include_tools)
        self.toggle_do_not_show_popup(do_not_show_again)

        # Create manually
        self.click_create_manually()

        logger.info("Manual assistant creation workflow completed")
