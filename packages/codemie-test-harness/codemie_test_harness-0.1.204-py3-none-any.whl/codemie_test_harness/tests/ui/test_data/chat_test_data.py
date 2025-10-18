"""
Test Data for Chat UI Tests

This module provides test data generation and management for chat-related UI tests.
Following best practices by separating test data from test logic and providing
reusable data factories for consistent testing.

Architecture follows the same patterns as other test data modules in the framework.
"""

from dataclasses import dataclass


@dataclass
class ChatTestMessage:
    """
    Data class for chat message test data.

    Encapsulates message content and metadata for chat testing scenarios.
    """

    content: str
    expected_response: str


class ChatTestDataFactory:
    """
    Factory class for generating chat test data.

    This factory provides various methods to create different types of
    chat test data for different testing scenarios.
    """

    @staticmethod
    def create_simple_test_message() -> ChatTestMessage:
        """
        Create a simple test message for basic chat functionality testing.

        Returns:
            ChatTestMessage: Simple test message data
        """
        return ChatTestMessage(
            content="Hello, this is a test message for chat functionality validation.",
            expected_response="",
        )

    @staticmethod
    def create_coding_help_message() -> ChatTestMessage:
        """
        Create a coding-related question message.
        """
        return ChatTestMessage(
            content="Hello, I need help with a coding question.",
            expected_response="",
        )

    @staticmethod
    def create_coding_question_message() -> ChatTestMessage:
        """
        Create a coding-related question message.
        """
        return ChatTestMessage(
            content="Can you help me understand Python decorators?",
            expected_response="",
        )


# ==================== CONVENIENCE FUNCTIONS ====================


def get_simple_test_message() -> ChatTestMessage:
    """Convenience function to get simple test message."""
    return ChatTestDataFactory.create_simple_test_message()


def get_coding_help_message() -> ChatTestMessage:
    """Convenience function to get coding help message."""
    return ChatTestDataFactory.create_coding_help_message()


def get_coding_question_message() -> ChatTestMessage:
    """Convenience function to get coding question message."""
    return ChatTestDataFactory.create_coding_question_message()


# ==================== TEST DATA CONSTANTS ====================

# Common test messages for reuse
COMMON_TEST_MESSAGES = {
    "hello": "Hello, how can you help me today?",
    "coding_help": "Can you help me debug this Python code?",
    "documentation": "Please help me write documentation for this API.",
    "code_review": "Can you review this code and suggest improvements?",
    "testing_help": "What are the best practices for unit testing?",
    "architecture": "How should I design a microservices architecture?",
}

LLM_ENGINES = ["Bedrock Claude 4 Sonnet"]
