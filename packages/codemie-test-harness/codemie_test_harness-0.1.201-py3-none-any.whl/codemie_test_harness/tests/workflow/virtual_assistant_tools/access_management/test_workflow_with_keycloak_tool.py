import pytest

from codemie_test_harness.tests.enums.tools import AccessManagementTool
from codemie_test_harness.tests.test_data.keycloak_tool_test_data import (
    KEYCLOAK_TOOL_PROMPT,
    KEYCLOAK_TOOL_RESPONSE,
)
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_tool_triggered,
)


@pytest.mark.workflow
@pytest.mark.virtual_workflow
@pytest.mark.keycloak
@pytest.mark.api
def test_workflow_with_virtual_assistant_with_keycloak_tool(
    keycloak_integration,
    workflow_with_virtual_assistant,
    workflow_utils,
    similarity_check,
):
    assistant_and_state_name = get_random_name()

    test_workflow = workflow_with_virtual_assistant(
        assistant_and_state_name,
        AccessManagementTool.KEYCLOAK,
        integration=keycloak_integration,
        task=KEYCLOAK_TOOL_PROMPT,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id, assistant_and_state_name
    )
    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        test_workflow
    )
    assert_tool_triggered(AccessManagementTool.KEYCLOAK, triggered_tools)
    similarity_check.check_similarity(response, KEYCLOAK_TOOL_RESPONSE)
