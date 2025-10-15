import pytest

from codemie_sdk.models.integration import CredentialTypes
from codemie_test_harness.tests.enums.tools import CodeBaseTool
from codemie_test_harness.tests.test_data.codebase_tools_test_data import (
    code_tools_test_data,
    sonar_tools_test_data,
)
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_tool_triggered,
)


@pytest.fixture(scope="module")
def code_datasource(integration_utils, datasource_utils, default_embedding_llm):
    """Fixture to create a code datasource for testing."""
    integration = integration_utils.create_integration(
        credential_type=CredentialTypes.GIT,
        credential_values=CredentialsManager.gitlab_credentials(),
    )
    datasource = datasource_utils.create_gitlab_datasource(
        setting_id=integration.id,
        embeddings_model=default_embedding_llm.base_name,
    )
    yield datasource
    if datasource:
        datasource_utils.delete_datasource(datasource)
    if integration:
        integration_utils.delete_integration(integration)


@pytest.mark.workflow
@pytest.mark.virtual_workflow
@pytest.mark.codebase
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-5456, EPMCDME-5427, EPMCDME-5466, EPMCDME-5442")
@pytest.mark.parametrize(
    "toolkit, tool_name, prompt, expected_response",
    code_tools_test_data,
    ids=[f"{row[1]}" for row in code_tools_test_data],
)
def test_workflow_with_codebase_tools(
    workflow_with_virtual_assistant,
    workflow_utils,
    code_datasource,
    similarity_check,
    toolkit,
    tool_name,
    prompt,
    expected_response,
):
    """Test workflow execution with codebase tools and datasource context."""

    assistant_and_state_name = get_random_name()
    test_workflow = workflow_with_virtual_assistant(
        assistant_and_state_name,
        tool_name,
        datasource_ids=[code_datasource.id],
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


@pytest.mark.workflow
@pytest.mark.virtual_workflow
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-5178")
@pytest.mark.parametrize(
    "toolkit, tool_name, credentials, prompt, expected_response",
    sonar_tools_test_data,
)
def test_workflow_with_sonar_tools(
    workflow_with_virtual_assistant,
    workflow_utils,
    integration_utils,
    similarity_check,
    toolkit,
    tool_name,
    credentials,
    prompt,
    expected_response,
):
    """Test workflow execution with Sonar tools (SonarQube/SonarCloud)."""
    assistant_and_state_name = get_random_name()

    integration = integration_utils.create_integration(
        CredentialTypes.SONAR, credentials
    )

    test_workflow = workflow_with_virtual_assistant(
        assistant_and_state_name,
        CodeBaseTool.SONAR,
        integration=integration,
        task=prompt,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id, assistant_and_state_name
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        test_workflow
    )
    assert_tool_triggered(CodeBaseTool.SONAR, triggered_tools)

    similarity_check.check_similarity(response, expected_response)
