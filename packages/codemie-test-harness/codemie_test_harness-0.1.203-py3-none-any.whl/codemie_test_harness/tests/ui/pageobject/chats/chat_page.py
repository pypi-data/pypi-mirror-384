"""
Chat Page Object for CodeMie UI Testing

This module implements the Chat page object following the established POM patterns
in the CodeMie test harness. It provides comprehensive support for chat functionality
including chat creation, message handling, and configuration management.

Following the same architecture as other page objects in the framework:
- Property-based element locators with multiple fallbacks
- Comprehensive verification methods
- Integration with ReportPortal via @step decorators
- Method chaining support for fluent API
- Robust error handling and graceful degradation
"""

from playwright.sync_api import expect, Locator
from reportportal_client import step

from codemie_test_harness.tests.ui import conversation_ids
from codemie_test_harness.tests.ui.pageobject.base_page import BasePage
from codemie_test_harness.tests.ui.pageobject.chats.configuration_panel import (
    ConfigurationPanel,
)


# noinspection PyArgumentList
class ChatPage(BasePage):
    """
    Chat page object with comprehensive chat functionality support.

    This class encapsulates all chat-related UI interactions including:
    - Chat creation and management
    - Message composition and sending
    - Configuration handling
    - Navigation and verification methods

    Follows established POM patterns with property-based locators and method chaining.
    """

    chat_id = None

    def __init__(self, page):
        super().__init__(page)
        self.page_url = "/#/chats"

    # ==================== CORE CHAT ELEMENTS ====================

    @property
    def new_chat_button(self) -> Locator:
        """Primary new chat button"""
        return self.page.locator("#new-chat")

    @property
    def chat_input(self) -> Locator:
        """Main chat input field with comprehensive selector strategy."""
        return self.page.locator(".ql-editor")

    @property
    def send_button(self) -> Locator:
        """Send message button."""
        return self.page.locator("button").filter(has_text="Send")

    @property
    def chat_history_container(self) -> Locator:
        """Container holding all chat messages."""
        return self.page.locator(".history")

    @property
    def user_message(self) -> Locator:
        """Individual user message element."""
        return self.chat_history_container.locator(".request")

    @property
    def assistant_message(self) -> Locator:
        """Individual user message element."""
        return self.chat_history_container.locator(".content")

    @property
    def processed_in_field(self) -> Locator:
        return self.chat_history_container.locator("span").filter(
            has_text="Processed in"
        )

    @property
    def search_assistant_list(self) -> Locator:
        return self.page.locator("#quill-mention-list")

    # ==================== ACTION BUTTONS ====================

    @property
    def action_buttons_bar(self) -> Locator:
        """Execution Info button with tooltip."""
        return self.page.locator("div.ml-auto")

    # ==================== CHAT HISTORY CONTAINER ACTION BUTTONS ====================

    @property
    def user_message_copy_button(self) -> Locator:
        """Copy button for user messages - first button in user message actions."""
        return self.chat_history_container.locator("a.chat-message-action").nth(0)

    @property
    def user_message_edit_button(self) -> Locator:
        """Edit button for user messages - second button in user message actions."""
        return self.chat_history_container.locator("a.chat-message-action").nth(1)

    @property
    def user_message_regenerate_button(self) -> Locator:
        """Regenerate/refresh button for user messages - third button in user message actions."""
        return self.chat_history_container.locator("a.chat-message-action").nth(2)

    @property
    def user_message_delete_button(self) -> Locator:
        """Delete button for user messages - fourth button in user message actions."""
        return self.chat_history_container.locator("a.chat-message-action").nth(3)

    @property
    def assistant_message_copy_button(self) -> Locator:
        """Copy button for assistant messages - first button in assistant message actions."""
        return self.chat_history_container.locator(
            ".action-buttons a.chat-message-action"
        ).nth(0)

    @property
    def assistant_message_edit_button(self) -> Locator:
        """Edit button for assistant messages - second button in assistant message actions."""
        return self.chat_history_container.locator(
            ".action-buttons a.chat-message-action"
        ).nth(1)

    @property
    def assistant_message_share_button(self) -> Locator:
        """Share/export button for assistant messages - button with up arrow icon."""
        return self.chat_history_container.locator(
            ".action-buttons button.button.tertiary.medium"
        )

    @property
    def execution_info_button(self) -> Locator:
        """Execution Info button with tooltip."""
        return self.action_buttons_bar.locator("button.button.secondary.medium").nth(0)

    @property
    def share_chat_button(self) -> Locator:
        """Share chat button with share icon."""
        return self.action_buttons_bar.locator("button.button.secondary.medium").nth(1)

    @property
    def export_chat_button(self) -> Locator:
        """Export chat button with export icon."""
        return self.action_buttons_bar.locator("button.button.secondary.medium").nth(2)

    @property
    def clear_chat_button(self) -> Locator:
        """Clear chat button with clear/delete icon."""
        return self.action_buttons_bar.locator("button.button.secondary.medium").nth(3)

    @property
    def add_attachment_button(self) -> Locator:
        """Add attachment button with paperclip icon."""
        return self.page.locator('button[aria-label*="attach"]')

    @property
    def start_conversation_invitation(self) -> Locator:
        """Start conversation invitation text and elements."""
        return self.page.locator("h1").filter(
            has_text="Start a conversation with an assistant"
        )

    @property
    def conversation_invitation_subtitle(self) -> Locator:
        """Conversation subtitle text."""
        return self.page.get_by_text(
            "Ask anything or type @ and choose assistant from the list"
        )

    # ==================== CONFIGURATION ELEMENTS ====================

    @property
    def configuration_button(self) -> Locator:
        """Configuration button with text and icon."""
        return self.page.locator("button").filter(has_text="Configuration")

    @property
    def chat_configuration_panel(self):
        """Chat configuration component."""
        return ConfigurationPanel(self.page)

    # ==================== CHAT HISTORY AND SIDEBAR ====================

    @property
    def chat_sidebar(self) -> Locator:
        """Chat history sidebar."""
        return self.page.locator("")

    @property
    def chat_history_items(self) -> Locator:
        """Individual chat history items in sidebar."""
        return self.chat_sidebar.locator("")

    # ==================== NAVIGATION METHODS ====================

    @step
    def navigate_to(self, chat_id: str):
        """Navigate to the main chat page."""
        self.page.goto(f"{self.page_url}/{chat_id}")
        self.wait_for_page_load()
        self.chat_id = chat_id
        return self

    @step
    def start_new_chat(self):
        """Start a new chat conversation."""
        if self.new_chat_button.is_visible():
            self.new_chat_button.click()
            self.wait_for_page_load()
            _id = self.get_id_from_url(self.evaluate_current_url())
            conversation_ids.append(_id)
            self.chat_id = _id
            return _id
        return None

    # ==================== ACTION BUTTON METHODS ====================

    @step
    def click_execution_info(self):
        """Click the execution info button."""
        self.execution_info_button.click()
        return self

    @step
    def click_share_chat(self):
        """Click the share chat button."""
        self.share_chat_button.click()
        return self

    @step
    def click_export_chat(self):
        """Click the export chat button."""
        self.export_chat_button.click()
        return self

    @step
    def click_clear_chat(self):
        """Click the clear chat button."""
        self.clear_chat_button.click()
        return self

    @step
    def click_add_attachment(self):
        """Click the add attachment button."""
        self.add_attachment_button.click()
        return self

    @step
    def click_configuration(self):
        """Click the configuration button."""
        self.configuration_button.click()
        return self

    @step
    def open_configuration(self):
        if not self.chat_configuration_panel.panel.is_visible():
            """Open the configuration panel."""
            self.click_configuration()
        return self

    @step
    def close_configuration(self):
        if self.chat_configuration_panel.panel.is_visible():
            """Close the configuration panel."""
            self.click_configuration()
        return self

    # ==================== CHAT INTERACTION METHODS ====================

    @step
    def send_message(self, message: str, assistant_name=""):
        """
        Send a message in the chat.

        Args:
            message: The message text to send
            assistant_name: assistant_name
        """
        if not assistant_name == "":
            self.chat_input.fill(f"@{assistant_name}")
            self.get_assistant_item_in_list(assistant_name).click()
            self.chat_input.type(message)
            self.send_button.click()
            return self
        else:
            self.chat_input.fill(message)
            self.send_button.click()
            return self

    @step
    def clear_chat_input(self):
        """Clear the chat input field."""
        self.chat_input.fill("")
        return self

    @step
    def type_message_without_sending(self, message: str):
        """Type a message without sending it."""
        self.chat_input.fill(message)
        return self

    @step
    def send_test_message(self, message: str = "Test message"):
        """Send a test message for verification purposes."""
        self.send_message(message)
        return self

    @step
    def get_assistant_item_in_list(self, name: str) -> Locator:
        return self.search_assistant_list.locator("p").filter(has_text=name)

    # ==================== ACTION BUTTON VERIFICATION METHODS ====================

    @step
    def should_have_execution_info_button_visible(self):
        """Verify that the execution info button is visible."""
        expect(self.execution_info_button).to_be_visible()
        return self

    @step
    def should_have_share_chat_button_visible(self):
        """Verify that the share chat button is visible."""
        expect(self.share_chat_button).to_be_visible()
        return self

    @step
    def should_have_export_chat_button_visible(self):
        """Verify that the export chat button is visible."""
        expect(self.export_chat_button).to_be_visible()
        return self

    @step
    def should_have_clear_chat_button_visible(self):
        """Verify that the clear chat button is visible."""
        expect(self.clear_chat_button).to_be_visible()
        return self

    @step
    def should_have_configuration_button_visible(self):
        """Verify that the configuration button is visible."""
        expect(self.configuration_button).to_be_visible()
        return self

    @step
    def should_have_add_attachment_button_visible(self):
        """Verify that the add attachment button is visible."""
        expect(self.add_attachment_button).to_be_visible()
        return self

    @step
    def should_have_start_conversation_invitation_visible(self):
        """Verify that the start conversation invitation is visible."""
        expect(self.start_conversation_invitation).to_be_visible()
        return self

    @step
    def should_have_conversation_subtitle_visible(self):
        """Verify that the conversation subtitle is visible."""
        expect(self.conversation_invitation_subtitle).to_be_visible()
        return self

    # ==================== CHAT HISTORY CONTAINER BUTTON VERIFICATION METHODS ====================

    @step
    def should_have_user_message_copy_button_visible(self):
        """Verify that the user message copy button is visible."""
        expect(self.user_message_copy_button).to_be_visible()
        return self

    @step
    def should_have_user_message_edit_button_visible(self):
        """Verify that the user message edit button is visible."""
        expect(self.user_message_edit_button).to_be_visible()
        return self

    @step
    def should_have_user_message_regenerate_button_visible(self):
        """Verify that the user message regenerate button is visible."""
        expect(self.user_message_regenerate_button).to_be_visible()
        return self

    @step
    def should_have_user_message_delete_button_visible(self):
        """Verify that the user message delete button is visible."""
        expect(self.user_message_delete_button).to_be_visible()
        return self

    @step
    def should_have_assistant_message_copy_button_visible(self):
        """Verify that the assistant message copy button is visible."""
        expect(self.assistant_message_copy_button).to_be_visible()
        return self

    @step
    def should_have_assistant_message_edit_button_visible(self):
        """Verify that the assistant message edit button is visible."""
        expect(self.assistant_message_edit_button).to_be_visible()
        return self

    @step
    def should_have_assistant_message_share_button_visible(self):
        """Verify that the assistant message share button is visible."""
        expect(self.assistant_message_share_button).to_be_visible()
        return self

    # ==================== VERIFICATION METHODS ====================

    @step
    def should_be_on_chat_page(self):
        """Verify that we are on the chat page."""
        expect(self.page).to_have_url(f"{self.page_url}/{self.chat_id}")
        return self

    @step
    def should_have_new_chat_button_visible(self):
        """Verify that the new chat button is visible."""
        expect(self.new_chat_button).to_be_visible()
        return self

    @step
    def should_have_chat_input_visible(self):
        """Verify that the chat input field is visible."""
        expect(self.chat_input).to_be_visible()
        return self

    @step
    def should_have_send_button_visible(self):
        """Verify that the send button is visible."""
        expect(self.send_button).to_be_visible()
        return self

    @step
    def should_have_send_button_enabled(self):
        """Verify that the send button is enabled."""
        expect(self.send_button).to_be_enabled()
        return self

    @step
    def should_have_send_button_disabled(self):
        """Verify that the send button is disabled."""
        expect(self.send_button).to_be_disabled()
        return self

    @step
    def should_have_message_sent(self, message_text: str):
        """
        Verify that a specific message was sent and appears in chat.

        Args:
            message_text: The message text to verify
        """
        message_locator = self.user_message.filter(has_text=message_text)
        expect(message_locator.first).to_be_visible()
        return self

    @step
    def should_have_assistant_response(self):
        """Verify that assistant has provided a response."""
        expect(self.assistant_message.first).to_be_visible()
        return self

    @step
    def should_have_new_chat_created(self):
        """Verify that a new chat has been successfully created."""
        # Check that we can interact with chat elements
        self.should_have_chat_input_visible()
        self.should_have_send_button_visible()

        # Verify that messages are visible (at least user message)
        expect(self.user_message.first).to_be_visible()
        return self

    @step
    def should_have_configuration_panel_opened(self):
        # Verify that configuration panel is opened
        expect(self.chat_configuration_panel.panel).to_be_visible()
        return self

    @step
    def should_have_configuration_panel_closed(self):
        # Verify that configuration panel is closed
        expect(self.chat_configuration_panel.panel).to_be_hidden()
        return self

    @step
    def should_have_history_visible(self):
        """Verify that the chat messages container is visible."""
        expect(self.chat_history_container).to_be_visible()
        return self

    @step
    def should_have_empty_chat_input(self):
        """Verify that the chat input field is empty."""
        expect(self.chat_input).to_have_text("")
        return self

    @step
    def should_have_chat_input_value(self, expected_value: str):
        """
        Verify that the chat input has a specific value.

        Args:
            expected_value: The expected input value
        """
        expect(self.chat_input).to_have_text(expected_value)
        return self

    @step
    def should_have_sidebar_visible(self):
        """Verify that the chat sidebar is visible."""
        expect(self.chat_sidebar).to_be_visible()
        return self

    @step
    def should_have_chat_history_items(self):
        """Verify that chat history items are present."""
        expect(self.chat_history_items.first).to_be_visible()
        return self

    # ==================== UTILITY METHODS ====================

    @step
    def get_user_message_count(self) -> int:
        """Get the number of user messages."""
        return self.user_message.count()

    @step
    def get_assistant_message_count(self) -> int:
        """Get the number of assistant messages."""
        return self.assistant_message.count()

    @step
    def get_last_user_message_text(self) -> str:
        """Get the text of the last user message."""
        return self.user_message.last.inner_text()

    @step
    def get_last_assistant_message_text(self) -> str:
        """Get the text of the last assistant message."""
        return self.assistant_message.last.inner_text()

    @step
    def get_chat_input_value(self) -> str:
        """Get the current value of the chat input field."""
        return self.chat_input.input_value()

    @step
    def wait_for_assistant_response(self, timeout: int = 30000):
        """
        Wait for assistant response to complete.

        Args:
            timeout: Timeout in milliseconds
        """
        self.processed_in_field.last.wait_for(state="visible", timeout=timeout)
        return self

    @step
    def scroll_to_bottom_of_chat(self):
        """Scroll to the bottom of the chat messages."""
        self.chat_history_container.evaluate(
            "element => element.scrollTop = element.scrollHeight"
        )
        return self

    @step
    def scroll_to_top_of_chat(self):
        """Scroll to the top of the chat messages."""
        self.chat_history_container.evaluate("element => element.scrollTop = 0")
        return self

    # ==================== INTEGRATION VERIFICATION ====================

    @step
    def verify_all_essential_elements_visible(self):
        """Comprehensive verification of all essential chat page elements."""
        self.should_have_new_chat_button_visible()
        self.should_have_chat_input_visible()
        self.should_have_send_button_visible()
        self.should_have_add_attachment_button_visible()
        self.should_have_configuration_button_visible()
        return self

    @step
    def verify_all_action_buttons_visible(self):
        """Verify all action buttons in the toolbar are visible."""
        self.should_have_execution_info_button_visible()
        self.should_have_share_chat_button_visible()
        self.should_have_export_chat_button_visible()
        self.should_have_clear_chat_button_visible()
        self.should_have_configuration_button_visible()
        return self

    @step
    def verify_empty_chat_state(self):
        """Verify the empty chat state with invitation message."""
        self.should_have_start_conversation_invitation_visible()
        self.should_have_conversation_subtitle_visible()
        self.should_have_chat_input_visible()
        self.should_have_send_button_visible()
        return self

    @step
    def verify_all_chat_history_action_buttons_visible(self):
        """Verify all 7 action buttons in chat history container are visible."""
        (
            self.should_have_user_message_copy_button_visible()
            .should_have_user_message_edit_button_visible()
            .should_have_user_message_regenerate_button_visible()
            .should_have_user_message_delete_button_visible()
            .should_have_assistant_message_copy_button_visible()
            .should_have_assistant_message_edit_button_visible()
            .should_have_assistant_message_share_button_visible()
        )
        return self
