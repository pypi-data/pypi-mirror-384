import pytest

from codemie_test_harness.tests.enums.tools import ProjectManagementTool
from codemie_test_harness.tests.test_data.pm_tools_test_data import (
    JIRA_TOOL_PROMPT,
    RESPONSE_FOR_JIRA_TOOL,
    CONFLUENCE_TOOL_PROMPT,
    RESPONSE_FOR_CONFLUENCE_TOOL,
    RESPONSE_FOR_JIRA_CLOUD_TOOL,
    JIRA_CLOUD_TOOL_PROMPT,
    CONFLUENCE_CLOUD_TOOL_PROMPT,
    RESPONSE_FOR_CONFLUENCE_CLOUD_TOOL,
)
from codemie_test_harness.tests.utils.constants import ProjectManagementIntegrationType

pm_tools_test_data = [
    pytest.param(
        ProjectManagementTool.JIRA,
        ProjectManagementIntegrationType.JIRA,
        JIRA_TOOL_PROMPT,
        RESPONSE_FOR_JIRA_TOOL,
        marks=pytest.mark.jira,
        id=ProjectManagementIntegrationType.JIRA,
    ),
    pytest.param(
        ProjectManagementTool.CONFLUENCE,
        ProjectManagementIntegrationType.CONFLUENCE,
        CONFLUENCE_TOOL_PROMPT,
        RESPONSE_FOR_CONFLUENCE_TOOL,
        marks=pytest.mark.confluence,
        id=ProjectManagementIntegrationType.CONFLUENCE,
    ),
    pytest.param(
        ProjectManagementTool.JIRA,
        ProjectManagementIntegrationType.JIRA_CLOUD,
        JIRA_CLOUD_TOOL_PROMPT,
        RESPONSE_FOR_JIRA_CLOUD_TOOL,
        marks=[pytest.mark.jira, pytest.mark.jira_cloud],
        id=ProjectManagementIntegrationType.JIRA_CLOUD,
    ),
    pytest.param(
        ProjectManagementTool.CONFLUENCE,
        ProjectManagementIntegrationType.CONFLUENCE_CLOUD,
        CONFLUENCE_CLOUD_TOOL_PROMPT,
        RESPONSE_FOR_CONFLUENCE_CLOUD_TOOL,
        marks=[pytest.mark.confluence, pytest.mark.confluence_cloud],
        id=ProjectManagementIntegrationType.CONFLUENCE_CLOUD,
    ),
]
