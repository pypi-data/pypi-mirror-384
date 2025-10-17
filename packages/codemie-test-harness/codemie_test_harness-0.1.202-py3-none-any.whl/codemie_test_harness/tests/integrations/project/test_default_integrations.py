import pytest

from codemie_sdk.models.integration import (
    IntegrationType,
    CredentialTypes,
)
from codemie_test_harness.tests.enums.tools import (
    Toolkit,
    NotificationTool,
    ProjectManagementTool,
    CodeBaseTool,
    AccessManagementTool,
    ReportPortalTool,
)
from codemie_test_harness.tests.test_data.ado_test_plan_tools_test_data import (
    ado_test_plan_get_test_data,
)
from codemie_test_harness.tests.test_data.cloud_tools_test_data import cloud_test_data
from codemie_test_harness.tests.test_data.codebase_tools_test_data import (
    sonar_tools_test_data,
)
from codemie_test_harness.tests.test_data.git_tools_test_data import (
    list_branches_set_active_branch_test_data,
)
from codemie_test_harness.tests.test_data.keycloak_tool_test_data import (
    KEYCLOAK_TOOL_PROMPT,
    KEYCLOAK_TOOL_RESPONSE,
)
from codemie_test_harness.tests.test_data.notification_tools_test_data import (
    EMAIL_TOOL_PROMPT,
    EMAIL_RESPONSE,
)
from codemie_test_harness.tests.test_data.pm_tools_test_data import (
    JIRA_TOOL_PROMPT,
    RESPONSE_FOR_JIRA_TOOL,
)
from codemie_test_harness.tests.test_data.report_portal_tools_test_data import (
    rp_test_data,
)
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.constants import test_project_name


@pytest.mark.assistant
@pytest.mark.cloud
@pytest.mark.integration
@pytest.mark.project_integration
@pytest.mark.default_integration
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-2377")
@pytest.mark.parametrize(
    "toolkit, tool_name, credential_type, credentials, prompt, expected_response",
    cloud_test_data,
)
def test_assistant_with_default_integration_cloud(
    general_integration,
    integration_utils,
    assistant,
    assistant_utils,
    toolkit,
    tool_name,
    credential_type,
    credentials,
    prompt,
    expected_response,
    similarity_check,
):
    #  delete existing integrations of the same type
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, credential_type, test_project_name
        )
    # create a new integration
    general_integration(
        integration_type=IntegrationType.PROJECT,
        credential_type=credential_type,
        credential_values=credentials,
        project_name=test_project_name,
    )
    # create an assistant
    cloud_assistant = assistant(toolkit, tool_name, project_name=test_project_name)

    response, triggered_tools = assistant_utils.ask_assistant(
        cloud_assistant, prompt, minimal_response=False
    )

    assert_tool_triggered(tool_name, triggered_tools)

    similarity_check.check_similarity(response, expected_response)


@pytest.mark.assistant
@pytest.mark.ado
@pytest.mark.integration
@pytest.mark.project_integration
@pytest.mark.default_integration
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-2377")
def test_assistant_with_default_integration_ado(
    general_integration,
    integration_utils,
    assistant,
    assistant_utils,
    similarity_check,
):
    # Test data
    toolkit = ado_test_plan_get_test_data[0][0]
    tool_name = ado_test_plan_get_test_data[0][1]
    prompt = ado_test_plan_get_test_data[0][2]
    expected_response = ado_test_plan_get_test_data[0][3]
    #  delete existing integrations of the same type
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.AZURE_DEVOPS
        )
    # create a new integration
    general_integration(
        integration_type=IntegrationType.PROJECT,
        credential_type=CredentialTypes.AZURE_DEVOPS,
        credential_values=CredentialsManager.azure_devops_credentials(),
        project_name=test_project_name,
    )
    # create an assistant
    ado_assistant = assistant(toolkit, tool_name, project_name=test_project_name)

    response, triggered_tools = assistant_utils.ask_assistant(
        ado_assistant, prompt, minimal_response=False
    )

    assert_tool_triggered(tool_name, triggered_tools)

    similarity_check.check_similarity(response, expected_response)


@pytest.mark.assistant
@pytest.mark.integration
@pytest.mark.project_integration
@pytest.mark.default_integration
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-2377")
@pytest.mark.parametrize(
    "toolkit, tool_name, credentials, prompt, expected_response",
    sonar_tools_test_data,
)
def test_assistant_with_default_integration_codebase(
    general_integration,
    integration_utils,
    assistant,
    assistant_utils,
    toolkit,
    tool_name,
    credentials,
    prompt,
    expected_response,
    similarity_check,
):
    #  delete existing integrations of the same type
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.SONAR, test_project_name
        )
    # create a new integration
    general_integration(
        integration_type=IntegrationType.PROJECT,
        credential_type=CredentialTypes.SONAR,
        credential_values=credentials,
        project_name=test_project_name,
    )
    # create an assistant
    sonar_assistant = assistant(
        toolkit, CodeBaseTool.SONAR, project_name=test_project_name
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        sonar_assistant, prompt, minimal_response=False
    )

    assert_tool_triggered(CodeBaseTool.SONAR, triggered_tools)

    similarity_check.check_similarity(response, expected_response)


@pytest.mark.assistant
@pytest.mark.gitlab
@pytest.mark.integration
@pytest.mark.project_integration
@pytest.mark.default_integration
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-2377")
def test_assistant_with_default_integration_git(
    general_integration,
    integration_utils,
    code_context,
    datasource_utils,
    assistant,
    assistant_utils,
    similarity_check,
    default_embedding_llm,
):
    # Test data
    toolkit = list_branches_set_active_branch_test_data[0][0]
    tool_name = list_branches_set_active_branch_test_data[0][1]
    prompt = list_branches_set_active_branch_test_data[0][2]
    expected_response = list_branches_set_active_branch_test_data[0][3]
    #  delete all existing integrations of the same type
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.GIT, test_project_name
        )
    # create a new integration
    _git_integration = general_integration(
        integration_type=IntegrationType.PROJECT,
        credential_type=CredentialTypes.GIT,
        credential_values=CredentialsManager.gitlab_credentials(),
        project_name=test_project_name,
    )
    # create a new datasource
    git_datasource = datasource_utils.create_gitlab_datasource(
        setting_id=_git_integration.id,
        embeddings_model=default_embedding_llm.base_name,
        project_name=test_project_name,
    )
    # create an assistant
    git_assistant = assistant(
        toolkit,
        tool_name,
        context=code_context(git_datasource),
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        git_assistant, prompt, minimal_response=False
    )

    assert_tool_triggered(tool_name, triggered_tools)

    similarity_check.check_similarity(response, expected_response)


@pytest.mark.assistant
@pytest.mark.jira
@pytest.mark.project_management
@pytest.mark.integration
@pytest.mark.project_integration
@pytest.mark.default_integration
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-2377")
def test_assistant_with_default_integration_jira(
    general_integration,
    integration_utils,
    assistant,
    assistant_utils,
    similarity_check,
):
    #  delete existing integrations of the same type
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.JIRA, test_project_name
        )
    # create a new integration
    general_integration(
        integration_type=IntegrationType.PROJECT,
        credential_type=CredentialTypes.JIRA,
        credential_values=CredentialsManager.jira_credentials(),
        project_name=test_project_name,
    )
    # create an assistant
    jira_assistant = assistant(
        Toolkit.PROJECT_MANAGEMENT,
        ProjectManagementTool.JIRA,
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        jira_assistant, JIRA_TOOL_PROMPT, minimal_response=False
    )

    assert_tool_triggered(ProjectManagementTool.JIRA, triggered_tools)

    similarity_check.check_similarity(response, RESPONSE_FOR_JIRA_TOOL)


@pytest.mark.assistant
@pytest.mark.email
@pytest.mark.notification
@pytest.mark.integration
@pytest.mark.project_integration
@pytest.mark.default_integration
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-2377")
def test_assistant_with_default_integration_email(
    general_integration,
    integration_utils,
    assistant,
    assistant_utils,
    similarity_check,
):
    #  delete existing integrations of the same type
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.EMAIL, test_project_name
        )
    # create a new integration
    general_integration(
        integration_type=IntegrationType.PROJECT,
        credential_type=CredentialTypes.EMAIL,
        credential_values=CredentialsManager.gmail_credentials(),
        project_name=test_project_name,
    )
    # create an assistant
    email_assistant = assistant(
        Toolkit.NOTIFICATION, NotificationTool.EMAIL, project_name=test_project_name
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        email_assistant, EMAIL_TOOL_PROMPT, minimal_response=False
    )

    assert_tool_triggered(NotificationTool.EMAIL, triggered_tools)

    similarity_check.check_similarity(response, EMAIL_RESPONSE)


@pytest.mark.assistant
@pytest.mark.keycloak
@pytest.mark.integration
@pytest.mark.project_integration
@pytest.mark.default_integration
@pytest.mark.api
def test_assistant_with_default_integration_keycloak(
    general_integration,
    integration_utils,
    assistant,
    assistant_utils,
    similarity_check,
):
    #  delete existing integrations of the same type
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.KEYCLOAK, test_project_name
        )
    # create a new integration
    general_integration(
        integration_type=IntegrationType.PROJECT,
        credential_type=CredentialTypes.KEYCLOAK,
        credential_values=CredentialsManager.keycloak_credentials(),
        project_name=test_project_name,
    )
    # create an assistant
    keycloak_assistant = assistant(
        Toolkit.ACCESS_MANAGEMENT,
        AccessManagementTool.KEYCLOAK,
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        keycloak_assistant, KEYCLOAK_TOOL_PROMPT, minimal_response=False
    )

    assert_tool_triggered(AccessManagementTool.KEYCLOAK, triggered_tools)

    similarity_check.check_similarity(response, KEYCLOAK_TOOL_RESPONSE)


@pytest.mark.assistant
@pytest.mark.report_portal
@pytest.mark.integration
@pytest.mark.project_integration
@pytest.mark.default_integration
@pytest.mark.api
def test_assistant_with_default_integration_report_portal(
    general_integration,
    integration_utils,
    assistant,
    assistant_utils,
    similarity_check,
):
    prompt = rp_test_data[7][2]
    expected_response = rp_test_data[7][3]

    #  delete existing integrations of the same type
    for integration_type in IntegrationType:
        integration_utils.delete_integrations_by_type(
            integration_type, CredentialTypes.REPORT_PORTAL, test_project_name
        )
    # create a new integration
    general_integration(
        integration_type=IntegrationType.PROJECT,
        credential_type=CredentialTypes.REPORT_PORTAL,
        credential_values=CredentialsManager.report_portal_credentials(),
        project_name=test_project_name,
    )
    # create an assistant
    report_portal_assistant = assistant(
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_DASHBOARD_DATA,
        project_name=test_project_name,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        report_portal_assistant, prompt, minimal_response=False
    )

    assert_tool_triggered(ReportPortalTool.GET_DASHBOARD_DATA, triggered_tools)

    similarity_check.check_similarity(response, expected_response)
