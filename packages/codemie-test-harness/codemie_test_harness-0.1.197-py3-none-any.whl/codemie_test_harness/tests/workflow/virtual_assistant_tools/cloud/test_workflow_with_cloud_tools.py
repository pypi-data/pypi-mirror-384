import pytest

from codemie_test_harness.tests.test_data.cloud_tools_test_data import cloud_test_data
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_tool_triggered,
)


@pytest.mark.workflow
@pytest.mark.virtual_workflow
@pytest.mark.cloud
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-5093")
@pytest.mark.testcase("EPMCDME-5136")
@pytest.mark.testcase("EPMCDME-5135")
@pytest.mark.parametrize(
    "toolkit, tool_name, credential_type, credentials, prompt, expected_response",
    cloud_test_data,
)
def test_workflow_with_cloud_tools(
    workflow_with_virtual_assistant,
    integration,
    workflow_utils,
    similarity_check,
    toolkit,
    tool_name,
    credential_type,
    credentials,
    prompt,
    expected_response,
):
    assistant_and_state_name = get_random_name()

    cloud_integration = integration(credential_type, credentials)

    test_workflow = workflow_with_virtual_assistant(
        assistant_and_state_name,
        tool_name,
        integration=cloud_integration,
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
