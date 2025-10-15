"""
Assistant Configure & Test Panel Component for CodeMie UI Testing
"""

from playwright.sync_api import expect, Locator
from reportportal_client import step


class ConfigureAndTestPanel:
    """
    Assistant Configure & Test side panel component with comprehensive configuration management.

    This component handles all configuration-related interactions including.

    Follows established POM patterns with property-based locators.
    """

    def __init__(self, page):
        self.page = page

    # ==================== PANEL CONTAINER ELEMENTS ====================

    @property
    def panel(self) -> Locator:
        """Panel main container."""
        return self.page.locator(".h-full .bg-sidebar")

    @property
    def panel_title(self) -> Locator:
        return self.panel.locator("h4")

    @property
    def cancel_button(self) -> Locator:
        return self.panel.locator("button").filter(has_text="Cancel")

    @property
    def save_button(self) -> Locator:
        return self.panel.locator("button").filter(has_text="Save")

    @property
    def system_prompt_current_section(self) -> Locator:
        """System Prompt current version section."""
        return self.panel.locator("div#current")

    @property
    def system_prompt_edit_field(self) -> Locator:
        """System Prompt editing field section."""
        return self.system_prompt_current_section.locator("textarea#system_prompt")

    # ==================== VERIFICATION METHODS ====================

    @step
    def should_be_visible(self):
        """Verify that the configuration panel is visible."""
        expect(self.panel).to_be_visible()
        return self

    @step
    def should_be_hidden(self):
        """Verify that the configuration panel is hidden."""
        expect(self.panel).to_be_hidden()
        return self

    @step
    def should_have_system_prompt_section_visible(self):
        """Verify that the System prompt section is visible."""
        expect(self.system_prompt_current_section).to_be_visible()
        return self

    @step
    def should_have_all_sections_visible(self):
        """Verify that all main panel sections are visible."""
        expect(self.panel_title).to_be_visible()
        expect(self.cancel_button).to_be_visible()
        expect(self.save_button).to_be_visible()
        self.should_have_system_prompt_section_visible()
        expect(self.system_prompt_edit_field).to_be_visible()
        return self

    @step
    def should_have_system_prompt(self, system_prompt_text: str):
        """Verify that the System prompt text matches param"""
        expect(self.system_prompt_edit_field).to_have_value(system_prompt_text)
        return self

    # ==================== INTERACTION METHODS ====================

    @step
    def update_system_prompt(self, new_sys_prompt: str):
        self.system_prompt_edit_field.clear()
        self.system_prompt_edit_field.fill(new_sys_prompt)
        return self

    @step
    def save_changes(self):
        self.save_button.click()
        return self

    @step
    def cancel_changes(self):
        self.cancel_button.click()
        return self
