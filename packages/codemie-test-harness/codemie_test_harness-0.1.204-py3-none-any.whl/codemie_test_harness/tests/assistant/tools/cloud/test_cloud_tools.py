import pytest

from codemie_test_harness.tests.test_data.cloud_tools_test_data import cloud_test_data

from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


@pytest.mark.assistant
@pytest.mark.cloud
@pytest.mark.api
@pytest.mark.parametrize(
    "toolkit,tool_name,credential_type,credentials,prompt,expected_response",
    cloud_test_data,
)
def test_assistant_with_cloud_tools(
    assistant_utils,
    assistant,
    integration_utils,
    similarity_check,
    toolkit,
    tool_name,
    credential_type,
    credentials,
    prompt,
    expected_response,
):
    settings = integration_utils.create_integration(credential_type, credentials)

    cloud_assistant = assistant(toolkit, tool_name, settings=settings)

    response, triggered_tools = assistant_utils.ask_assistant(
        cloud_assistant, prompt, minimal_response=False
    )

    assert_tool_triggered(tool_name, triggered_tools)

    similarity_check.check_similarity(response, expected_response)
