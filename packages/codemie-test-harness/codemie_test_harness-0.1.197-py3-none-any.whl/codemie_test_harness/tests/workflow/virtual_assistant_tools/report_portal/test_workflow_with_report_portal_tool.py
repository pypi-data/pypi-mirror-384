import pytest

from codemie_test_harness.tests.test_data.report_portal_tools_test_data import (
    rp_test_data,
)
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_tool_triggered,
)


@pytest.mark.workflow
@pytest.mark.virtual_workflow
@pytest.mark.report_portal
@pytest.mark.api
@pytest.mark.parametrize(
    "toolkit,tool_name,prompt,expected_response",
    rp_test_data,
    ids=[f"{row[0]}_{row[1]}" for row in rp_test_data],
)
def test_workflow_with_virtual_assistant_with_report_portal_tools(
    workflow_with_virtual_assistant,
    workflow_utils,
    report_portal_integration,
    similarity_check,
    toolkit,
    tool_name,
    prompt,
    expected_response,
):
    assistant_and_state_name = get_random_name()

    test_workflow = workflow_with_virtual_assistant(
        assistant_and_state_name,
        tool_name,
        integration=report_portal_integration,
        task=prompt,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id, assistant_and_state_name
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        test_workflow
    )
    assert_tool_triggered(tool_name, triggered_tools)

    similarity_check.check_similarity(response, expected_response)
