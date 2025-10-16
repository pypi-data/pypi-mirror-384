import pytest

from codemie_test_harness.tests.enums.tools import ServiceNowTool
from codemie_test_harness.tests.test_data.servicenow_tools_test_data import (
    PROMPT,
    EXPECTED_RESPONSE,
)
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_tool_triggered,
)


@pytest.mark.workflow
@pytest.mark.virtual_workflow
@pytest.mark.servicenow
@pytest.mark.api
def test_workflow_with_virtual_assistant_with_servicenow_tools(
    service_now_integration,
    workflow_with_virtual_assistant,
    workflow_utils,
    similarity_check,
):
    assistant_and_state_name = get_random_name()

    test_workflow = workflow_with_virtual_assistant(
        assistant_and_state_name,
        ServiceNowTool.SERVICE_NOW,
        integration=service_now_integration,
        task=PROMPT,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id, assistant_and_state_name
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        test_workflow
    )
    assert_tool_triggered(ServiceNowTool.SERVICE_NOW, triggered_tools)

    similarity_check.check_similarity(response, EXPECTED_RESPONSE, 80)
