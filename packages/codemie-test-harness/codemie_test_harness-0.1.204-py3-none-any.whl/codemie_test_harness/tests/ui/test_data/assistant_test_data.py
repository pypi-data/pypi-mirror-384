"""
Test Data for Assistant UI Tests

This module provides test data generation and management for assistant-related UI tests.
Following best practices by separating test data from test logic and providing
reusable data factories for consistent testing.
"""

from dataclasses import dataclass
from typing import Optional, List

from codemie_test_harness.tests.utils.base_utils import get_random_name


@dataclass
class AssistantTestData:
    """
    Data class for assistant test data.

    This class encapsulates all the data needed for assistant creation tests,
    providing a clean and type-safe way to manage test data.
    """

    name: str
    description: str
    system_prompt: str
    icon_url: Optional[str] = None
    shared: bool = False


class AssistantTestDataFactory:
    """
    Factory class for generating assistant test data.

    This factory provides various methods to create different types of
    assistant test data for different testing scenarios.
    """

    @staticmethod
    def create_minimal_assistant_data() -> AssistantTestData:
        """
        Create minimal assistant data with only required fields.

        This represents the most basic assistant creation scenario
        with minimal required information.

        Returns:
            AssistantTestData: Minimal assistant test data
        """
        return AssistantTestData(
            name=f"QA Test Assistant {get_random_name()}",
            description="Minimal test assistant for QA automation.",
            system_prompt=(
                "You are a test assistant created for QA validation purposes. "
                "Provide helpful and accurate responses to user queries."
            ),
            shared=False,
            icon_url=ICON_URL,
        )

    @staticmethod
    def create_shared_assistant_data() -> AssistantTestData:
        """
        Create shared assistant data for public/shared testing scenarios.

        Returns:
            AssistantTestData: Shared assistant test data
        """
        return AssistantTestData(
            name=f"QA Shared Assistant {get_random_name()}",
            description="Shared QA assistant available to all team members",
            system_prompt=(
                "You are a shared QA assistant available to the entire team. "
                "Provide collaborative testing support, knowledge sharing, and "
                "help maintain consistent quality standards across projects."
            ),
            icon_url=ICON_URL,
            shared=True,
        )

    @staticmethod
    def create_validation_test_data() -> List[AssistantTestData]:
        """
        Create a list of assistant data for validation testing scenarios.

        This includes data for testing various validation scenarios,
        edge cases in form validation, and error handling.

        Returns:
            List[AssistantTestData]: List of validation test data
        """
        return [
            # Empty name scenario
            AssistantTestData(
                name="",
                description="Test description",
                system_prompt="Test prompt",
            ),
            # Long name scenario
            AssistantTestData(
                name="A" * 100,  # Very long name
                description="Test description for long name validation",
                system_prompt="Test prompt for long name scenario",
            ),
            # Empty description scenario
            AssistantTestData(
                name="Test Assistant",
                description="",
                system_prompt="Test prompt",
            ),
            # Empty system prompt scenario
            AssistantTestData(
                name="Test Assistant",
                description="Test description",
                system_prompt="",
            ),
        ]


class AssistantValidationRules:
    """
    Validation rules and constraints for assistant data.

    This class defines the validation rules that should be applied
    to assistant data during testing.
    """

    # Field length constraints
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_ICON_URL_LENGTH = 500

    # Required fields
    REQUIRED_FIELDS = ["name", "description", "system_prompt"]

    # Validation error messages (expected messages for testing)
    ERROR_MESSAGES = {
        "name_required": "Name is required",
        "name_too_long": f"Name must be less than {MAX_NAME_LENGTH} characters",
        "description_required": "Description is required",
        "description_too_long": f"Description must be less than {MAX_DESCRIPTION_LENGTH} characters",
        "system_prompt_required": "System prompt is required",
        "invalid_url": "Please enter a valid URL",
        "invalid_type": "Please select a valid assistant type",
    }


# ==================== CONVENIENCE FUNCTIONS ====================


def get_minimal_assistant_data() -> AssistantTestData:
    """Convenience function to get minimal assistant data."""
    return AssistantTestDataFactory.create_minimal_assistant_data()


def get_shared_assistant_data() -> AssistantTestData:
    """Convenience function to get shared assistant data."""
    return AssistantTestDataFactory.create_shared_assistant_data()


def get_validation_test_data() -> List[AssistantTestData]:
    """Convenience function to get validation test data."""
    return AssistantTestDataFactory.create_validation_test_data()


# ==================== TEST DATA CONSTANTS ====================

# Common test values for reuse
COMMON_TEST_PROMPTS = {
    "qa_assistant": (
        "You are a QA testing assistant. Your primary role is to help with "
        "quality assurance tasks, test automation, and ensuring software quality. "
        "Provide detailed and actionable guidance."
    ),
    "general_assistant": (
        "You are a helpful assistant. Provide clear, accurate, and helpful "
        "responses to user queries. Always be polite and professional."
    ),
    "specialist_assistant": (
        "You are a specialist assistant with deep expertise in your domain. "
        "Provide expert-level guidance and detailed technical solutions."
    ),
}

COMMON_TEST_DESCRIPTIONS = {
    "qa_assistant": "QA testing assistant for automation and quality assurance tasks",
    "general_assistant": "General purpose assistant for various tasks and queries",
    "specialist_assistant": "Specialist assistant with domain-specific expertise",
}

COMMON_ICON_URLS = {
    "qa_icon": "https://example.com/qa-assistant-icon.png",
    "general_icon": "https://example.com/general-assistant-icon.png",
    "specialist_icon": "https://example.com/specialist-assistant-icon.png",
}

ICON_URL = "https://raw.githubusercontent.com/epam-gen-ai-run/ai-run-install/main/docs/assets/ai/AQAUiTestGenerator.png"

GENERAL_PROMPT = "You are a helpful integration test assistant"
