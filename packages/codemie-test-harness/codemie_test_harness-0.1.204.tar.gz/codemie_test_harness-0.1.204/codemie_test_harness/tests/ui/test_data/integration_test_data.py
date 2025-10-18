"""
Helper utilities for integration UI tests.
Contains reusable functions and data generators for integration testing.
"""

from dataclasses import dataclass
from typing import Dict, Any

from codemie_sdk.models.integration import CredentialTypes

from codemie_test_harness.tests import PROJECT
from codemie_test_harness.tests.utils.base_utils import get_random_name


@dataclass
class IntegrationTestData:
    """Data class for integration form fields."""

    project: str
    alias: str
    description: str
    credential_type: CredentialTypes
    is_global: bool = False
    fields: Dict[str, Any] = None

    def __post_init__(self):
        if self.fields is None:
            self.fields = {}


class IntegrationTestDataFactory:
    @staticmethod
    def jira_integration() -> IntegrationTestData:
        return IntegrationTestData(
            project=PROJECT,
            alias=f"JIRA Server Integration {get_random_name()}",
            description="JIRA Server integration for project management",
            credential_type=CredentialTypes.JIRA,
            fields={
                "url": "https://jira.company.com",
                "username": "test.user@company.com",
                "token": "secure_password",
            },
        )

    @staticmethod
    def jira_cloud_integration() -> IntegrationTestData:
        return IntegrationTestData(
            project=PROJECT,
            alias=f"JIRA Cloud Integration {get_random_name()}",
            description="JIRA Cloud integration with API token",
            credential_type=CredentialTypes.JIRA,
            fields={
                "url": "https://jiraeu.epam.com",
                "username": "test.user@company.com",
                "token": "ATATT3xFfGF0...",
                "is_cloud": True,
            },
        )

    @staticmethod
    def git_integration() -> IntegrationTestData:
        return IntegrationTestData(
            project=PROJECT,
            alias=f"GitLab Integration {get_random_name()}",
            description="GitLab integration for code repository access",
            credential_type=CredentialTypes.GIT,
            fields={
                "url": "https://gitlab.company.com",
                "token": "glpat-1234567890abcdef",
            },
        )

    @staticmethod
    def confluence_integration() -> IntegrationTestData:
        return IntegrationTestData(
            project=PROJECT,
            alias=f"Confluence Integration {get_random_name()}",
            description="Confluence integration for project management",
            credential_type=CredentialTypes.CONFLUENCE,
            fields={
                "url": "https://kb.epam.com",
                "username": "test.user@company.com",
                "token": "secure_password",
                "is_cloud": False,
            },
        )

    @staticmethod
    def confluence_cloud_integration() -> IntegrationTestData:
        return IntegrationTestData(
            project=PROJECT,
            alias=f"Confluence Cloud Integration {get_random_name()}",
            description="Confluence Cloud integration for project management",
            credential_type=CredentialTypes.CONFLUENCE,
            fields={
                "url": "https://company.atlassian.net",
                "username": "test.user@company.com",
                "token": "ATATT3xFfGF0...",
                "is_cloud": True,
            },
        )

    # Expected validation messages
    validation_messages = {
        "invalid_email": "Please enter a valid email address",
        "invalid_url": "Please enter a valid URL",
        "duplicate_name": "An integration with this name already exists",
        "connection_failed": "Connection test failed",
        "connection_timeout": "Connection timeout",
        "cannot_create_setting": "Cannot create specified setting",
        "alias_required": "Alias is required",
    }

    # Success messages
    success_messages = {
        "integration_created": "Integration created successfully",
        "integration_updated": "Integration updated successfully",
        "connection_test_passed": "Connection test passed",
        "integration_deleted": "Integration deleted successfully",
    }
