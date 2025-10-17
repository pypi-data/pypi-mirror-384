"""
UI Test Suite for Chat Feature - Critical Happy Path Scenarios

This test suite implements UI automated tests for the "chat" feature
following Page Object Model (POM) best practices as specified in JIRA ticket EPMCDME-8305.

Test Coverage:
- Critical happy path for chat creation workflow
- Message sending and receiving functionality
- Basic chat interface interactions
- Navigation and UI component verification

Exclusions (as per requirements):
- Edge cases and negative scenarios
- Advanced error handling scenarios
- Complex multi-user scenarios

Architecture:
- Follows Page Object Model (POM) pattern
- Reusable UI components abstracted into dedicated classes
- Comprehensive locator strategies with fallbacks
- Property-based element access for maintainability
- Integration with ChatConfigurationModal component
"""

import pytest
from hamcrest import equal_to, assert_that

from codemie_test_harness.tests.ui.pageobject.chats.chats_sidebar import ChatsSidebar
from codemie_test_harness.tests.ui.test_data.chat_test_data import (
    get_simple_test_message,
    get_coding_question_message,
    get_coding_help_message,
)


# noinspection PyArgumentList
class TestChatPageElements:
    """Test suite for Chat page element visibility and structure."""

    @pytest.mark.chat
    @pytest.mark.ui
    def test_chat_page_elements_visibility(self, page, navigate_to_new_chat_page):
        """
        Test that all main elements are visible on Chat page.

        This test verifies the basic page structure and essential UI components
        are properly rendered and accessible to users.

        Critical Elements Verified:
        - Chat input field and send button
        - Messages container
        - Configuration access
        - Navigation elements
        """
        chat_page = navigate_to_new_chat_page(page)

        # Verify common page components
        chat_page.should_have_page_content_visible()
        chat_page.should_not_have_loading_indicator()

        # Verify we are on the correct page
        chat_page.should_be_on_chat_page()

        # Verify essential chat elements are visible
        chat_page.verify_all_essential_elements_visible()
        chat_page.verify_all_action_buttons_visible()

    @pytest.mark.chat
    @pytest.mark.ui
    def test_new_chat_button_visibility_and_interaction(
        self, page, navigate_to_new_chat_page
    ):
        """
        Test new chat button visibility and basic interaction.

        This test verifies that users can access the new chat functionality
        and that the button responds appropriately to user interaction.

        Interaction Flow:
        1. Navigate to chat page
        2. Verify new chat button is visible
        3. Test new chat button interaction
        4. Verify chat interface is ready for use
        """
        chat_page = navigate_to_new_chat_page(page)

        # Verify new chat button is accessible
        chat_page.should_have_new_chat_button_visible()

        # Test new chat interaction
        chat_page.start_new_chat()

        # Verify we are on the correct page
        chat_page.should_be_on_chat_page()

        # Verify chat interface is ready
        chat_page.should_have_chat_input_visible()
        chat_page.should_have_send_button_visible()

    @pytest.mark.chat
    @pytest.mark.ui
    def test_chats_sidebar_elements(self, page, navigate_to_new_chat_page):
        """
        Test chats sidebar elements.

        This test verifies that the chat history sidebar is accessible.

        Sidebar Tests:
        - Sidebar visibility
        - Chat item name
        """
        chat_page = navigate_to_new_chat_page(page)

        chat_page.start_new_chat()

        # Verify Sidebar
        chats_sidebar = ChatsSidebar(page)
        chats_sidebar.verify_all_sidebar_sections_visibility()
        assert_that(chats_sidebar.get_active_chat_title(), equal_to("New chat"))


# noinspection PyArgumentList
class TestChatInputAndSending:
    """Test suite for chat input field and message sending functionality."""

    @pytest.mark.chat
    @pytest.mark.ui
    def test_chat_input_field_interactions(self, page, navigate_to_new_chat_page):
        """
        Test chat input field interactions and input handling.

        This test verifies that users can successfully interact with the
        chat input field and that input values are properly handled.

        Input Field Tests:
        - Text input and retention
        - Input clearing functionality
        - Input field state management
        """
        chat_page = navigate_to_new_chat_page(page)

        # Test input field interaction
        test_message = get_simple_test_message()
        chat_page.type_message_without_sending(test_message.content)
        chat_page.should_have_chat_input_value(test_message.content)
        chat_page.should_have_send_button_visible()

        # Test input clearing
        chat_page.clear_chat_input()
        chat_page.should_have_empty_chat_input()

    @pytest.mark.chat
    @pytest.mark.ui
    def test_message_sending_functionality(self, page, navigate_to_new_chat_page):
        """
        Test message sending functionality with different message types.

        This test verifies that different types of messages can be sent
        successfully and that the chat interface handles them appropriately.
        """
        chat_page = navigate_to_new_chat_page(page)

        # Send the test message
        test_message = get_simple_test_message()
        chat_page.send_message(test_message.content)

        # Verify message was sent and appears in chat
        chat_page.should_have_history_visible()
        chat_page.should_have_message_sent(test_message.content)

        # Verify assistant response is appeared
        chat_page.wait_for_assistant_response()
        chat_page.should_have_assistant_response()

    @pytest.mark.chat
    @pytest.mark.ui
    def test_multiple_messages_workflow(self, page, navigate_to_new_chat_page):
        """
        Test sending multiple messages in sequence.

        This test verifies that the chat can handle multiple messages
        and maintains proper conversation flow.

        Multi-Message Flow:
        1. Send initial message
        2. Send follow-up message
        3. Verify both messages are preserved
        4. Verify conversation continuity
        """
        chat_page = navigate_to_new_chat_page(page)

        # Send first message
        first_message = get_coding_help_message()
        chat_page.send_message(first_message.content)
        chat_page.should_have_message_sent(first_message.content)
        chat_page.wait_for_assistant_response()

        # Send second message
        second_message = get_coding_question_message()
        chat_page.send_message(second_message.content)
        chat_page.should_have_message_sent(second_message.content)
        chat_page.wait_for_assistant_response()

        # Verify both messages are present
        user_messages = chat_page.get_user_message_count()
        assistant_messages = chat_page.get_assistant_message_count()
        assert_that(user_messages, equal_to(2))
        assert_that(assistant_messages, equal_to(2))

    @pytest.mark.chat
    @pytest.mark.ui
    def test_chat_history_action_buttons_visibility(
        self, page, navigate_to_new_chat_page
    ):
        chat_page = navigate_to_new_chat_page(page)
        test_message = get_simple_test_message()
        chat_page.send_message(test_message.content)
        chat_page.wait_for_assistant_response()

        # Verify chat messages action buttons
        chat_page.verify_all_chat_history_action_buttons_visible()
