"""
Chat Configuration Panel Component for CodeMie UI Testing

This module implements the chat configuration side panel component following the established
POM patterns. It provides comprehensive support for configuration management including
LLM engine selection, assistant management, and configuration testing.

Architecture follows the same patterns as other panel components:
- Property-based element locators with precise unique selectors
- Method chaining support for fluent API
- ReportPortal integration via @step decorators
- Comprehensive verification methods
"""

from playwright.sync_api import expect, Locator
from reportportal_client import step

from codemie_test_harness.tests.ui.pageobject.chats.configure_and_test_panel import (
    ConfigureAndTestPanel,
)


class ConfigurationPanel:
    """
    Chat configuration side panel component with comprehensive configuration management.

    This component handles all configuration-related interactions including:
    - Managing LLM engine selection
    - Interacting with connected assistants
    - Configuring and testing assistants
    - Verification of configuration states

    Follows established POM patterns with property-based locators.
    """

    def __init__(self, page):
        self.page = page

    # ==================== PANEL CONTAINER ELEMENTS ====================

    @property
    def panel(self) -> Locator:
        """Main configuration panel container."""
        # Using data-v attribute with class combination for uniqueness
        return self.page.locator(".chat-info")

    @property
    def general_section(self) -> Locator:
        """General configuration section."""
        return self.panel.locator("h3").filter(has_text="General")

    @property
    def connected_assistants_section(self) -> Locator:
        """Connected Assistants section."""
        return self.panel.locator("div").filter(has_text="Connected Assistants")

    # ==================== LLM ENGINE CONFIGURATION ====================

    @property
    def primary_llm_engine_label(self) -> Locator:
        """Primary LLM Engine label."""
        return self.panel.locator('label[for="model_type"].text-xs.text-text-tertiary')

    @property
    def primary_llm_engine_dropdown(self) -> Locator:
        """Primary LLM Engine dropdown selector."""
        return self.panel.locator('div.p-multiselect[id="model_type"]')

    @property
    def llm_engine_dropdown_trigger(self) -> Locator:
        """LLM Engine dropdown trigger button."""
        return self.primary_llm_engine_dropdown.locator(
            'div[data-pc-section="trigger"]'
        )

    @property
    def llm_engine_current_selection(self) -> Locator:
        """Current LLM Engine selection display."""
        return self.primary_llm_engine_dropdown.locator('div[data-pc-section="label"]')

    # ==================== ASSISTANT LIST ELEMENTS ====================
    class ConnectedAssistantCard:
        def __init__(self, page, title: str):
            self.page = page
            # Target assistant card by finding the card that contains the title
            self.assistant_card = self.page.locator(".assistant-list-item").filter(
                has=self.page.locator(".font-semibold.text-base").filter(
                    has_text=f"{title}"
                )
            )
            # ID field is the element with tooltip that contains the ID
            self.id_field = self.assistant_card.locator(
                "div.text-text-tertiary[data-pd-tooltip]"
            ).first
            # Link field is the assistant link element with tooltip
            self.link_field = self.assistant_card.locator(
                "div.assistant-link[data-pd-tooltip]"
            )
            # Config button is the button with "Configure & Test" text
            self.config_button = self.assistant_card.locator("button").filter(
                has_text="Configure"
            )

    @property
    def assistant_list(self) -> Locator:
        """Container for all assistant list items."""
        return self.panel.locator("div.assistant-list")

    # ==================== PANEL INTERACTION METHODS ====================

    @step
    def open_llm_engine_dropdown(self):
        """Open the Primary LLM Engine dropdown."""
        if self.primary_llm_engine_dropdown.is_visible():
            self.llm_engine_dropdown_trigger.click()
            self.page.wait_for_timeout(1000)
        return self

    @step
    def select_llm_engine_option(self, llm_name: str):
        """Select an option from the LLM Engine dropdown."""
        self.open_llm_engine_dropdown()

        search_input = self.page.locator(".p-multiselect-filter")
        search_input.fill(llm_name)
        option_item = self.page.locator(f'[aria-label="{llm_name}"]')
        if option_item.is_visible():
            option_item.click()
        else:
            raise Exception(f"'{llm_name} LLM is not found!")

        return self

    @step
    def open_assistant_configuration(self, assistant_name: str):
        assistant_card = self.ConnectedAssistantCard(
            page=self.page, title=assistant_name
        )
        assistant_card.config_button.click()
        return ConfigureAndTestPanel(self.page)

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
    def should_have_general_section_visible(self):
        """Verify that the General section is visible."""
        expect(self.general_section).to_be_visible()
        return self

    @step
    def should_have_connected_assistants_section_visible(self):
        """Verify that the Connected Assistants section is visible."""
        expect(self.connected_assistants_section).to_be_visible()
        return self

    @step
    def should_have_llm_engine_dropdown_visible(self):
        """Verify that the Primary LLM Engine dropdown is visible."""
        expect(self.primary_llm_engine_dropdown).to_be_visible()
        return self

    @step
    def should_have_llm_engine_selection(self, expected_text: str):
        """
        Verify the LLM Engine dropdown shows expected selection.

        Args:
            expected_text: Expected selection text (e.g., "Default: GPT-4.1 2025-04-14")
        """
        expect(self.llm_engine_current_selection).to_contain_text(expected_text)
        return self

    @step
    def should_have_assistant_list_visible(
        self,
    ):
        expect(self.assistant_list).to_be_visible()
        return self

    @step
    def should_have_assistant_visible(self, assistant_name: str):
        """
        Verify that a specific assistant is visible.

        Args:
            assistant_name: Name of the assistant to verify
        """
        assistant_card = self.ConnectedAssistantCard(
            page=self.page, title=assistant_name
        )
        expect(assistant_card.id_field).to_be_visible()
        expect(assistant_card.link_field).to_be_visible()
        expect(assistant_card.config_button).to_be_visible()
        return self

    @step
    def should_have_all_sections_visible(self):
        """Verify that all main panel sections are visible."""
        self.should_have_general_section_visible()
        self.should_have_connected_assistants_section_visible()
        self.should_have_llm_engine_dropdown_visible()
        self.should_have_assistant_list_visible()
        self.should_have_assistant_visible("AI/Run Chatbot")
        return self

    # ==================== UTILITY METHODS ====================

    @step
    def is_visible(self) -> bool:
        """Check if the configuration panel is currently visible."""
        return self.panel.is_visible()

    @step
    def get_current_llm_engine_selection(self) -> str:
        """Get the current LLM Engine selection text."""
        return self.llm_engine_current_selection.text_content()
