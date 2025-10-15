import pytest

from codemie_test_harness.tests.enums.tools import Toolkit, AccessManagementTool
from codemie_test_harness.tests.test_data.keycloak_tool_test_data import (
    KEYCLOAK_TOOL_PROMPT,
    KEYCLOAK_TOOL_RESPONSE,
)
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.keycloak
@pytest.mark.api
def test_workflow_with_assistant_with_keycloak_tool(
    assistant,
    workflow_with_assistant,
    workflow_utils,
    keycloak_integration,
    similarity_check,
):
    assistant = assistant(
        Toolkit.ACCESS_MANAGEMENT,
        AccessManagementTool.KEYCLOAK,
        settings=keycloak_integration,
    )

    workflow_with_assistant = workflow_with_assistant(assistant, KEYCLOAK_TOOL_PROMPT)
    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(AccessManagementTool.KEYCLOAK, triggered_tools)

    similarity_check.check_similarity(response, KEYCLOAK_TOOL_RESPONSE)
