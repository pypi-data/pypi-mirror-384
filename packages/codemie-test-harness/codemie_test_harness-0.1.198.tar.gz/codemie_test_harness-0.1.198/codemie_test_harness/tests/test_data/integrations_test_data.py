import pytest

from codemie_sdk.models.integration import CredentialTypes, CredentialValues
from codemie_test_harness.tests.enums.integrations import DataBaseDialect
from codemie_test_harness.tests.enums.tools import (
    Toolkit,
    VcsTool,
    NotificationTool,
    ProjectManagementTool,
    ServiceNowTool,
    OpenApiTool,
)
from codemie_test_harness.tests.test_data.notification_tools_test_data import (
    EMAIL_TOOL_PROMPT,
    TELEGRAM_TOOL_PROMPT,
)
from codemie_test_harness.tests.test_data.open_api_tools_test_data import (
    OPEN_API_SPEC_TOOL_TASK,
)
from codemie_test_harness.tests.test_data.pm_tools_test_data import (
    JIRA_TOOL_PROMPT,
    CONFLUENCE_TOOL_PROMPT,
)
from codemie_test_harness.tests.test_data.servicenow_tools_test_data import PROMPT
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.env_resolver import EnvironmentResolver

valid_integrations = [
    pytest.param(
        CredentialTypes.AWS,
        CredentialsManager.aws_credentials(),
        marks=[
            pytest.mark.aws,
            pytest.mark.cloud,
        ],
        id=CredentialTypes.AWS,
    ),
    pytest.param(
        CredentialTypes.AZURE,
        CredentialsManager.azure_credentials(),
        marks=[
            pytest.mark.azure,
            pytest.mark.cloud,
        ],
        id=CredentialTypes.AZURE,
    ),
    pytest.param(
        CredentialTypes.GCP,
        CredentialsManager.gcp_credentials(),
        marks=[
            pytest.mark.gcp,
            pytest.mark.cloud,
            pytest.mark.skipif(
                EnvironmentResolver.is_azure(),
                reason="Still have an issue with encoding long strings",
            ),
        ],
        id=CredentialTypes.GCP,
    ),
    pytest.param(
        CredentialTypes.SONAR,
        CredentialsManager.sonar_credentials(),
        marks=pytest.mark.sonar,
        id=f"{CredentialTypes.SONAR}_server",
    ),
    pytest.param(
        CredentialTypes.SONAR,
        CredentialsManager.sonar_cloud_credentials(),
        marks=pytest.mark.sonar,
        id=f"{CredentialTypes.SONAR}_cloud",
    ),
    pytest.param(
        CredentialTypes.GIT,
        CredentialsManager.gitlab_credentials(),
        marks=pytest.mark.gitlab,
        id=f"{CredentialTypes.GIT}_gitlab",
    ),
    pytest.param(
        CredentialTypes.GIT,
        CredentialsManager.github_credentials(),
        marks=pytest.mark.github,
        id=f"{CredentialTypes.GIT}_github",
    ),
    pytest.param(
        CredentialTypes.CONFLUENCE,
        CredentialsManager.confluence_credentials(),
        marks=[
            pytest.mark.confluence,
            pytest.mark.project_management,
        ],
        id=f"{CredentialTypes.CONFLUENCE}_server",
    ),
    pytest.param(
        CredentialTypes.CONFLUENCE,
        CredentialsManager.confluence_cloud_credentials(),
        marks=[
            pytest.mark.confluence,
            pytest.mark.confluence_cloud,
            pytest.mark.project_management,
        ],
        id=f"{CredentialTypes.CONFLUENCE}_cloud",
    ),
    pytest.param(
        CredentialTypes.JIRA,
        CredentialsManager.jira_credentials(),
        marks=[
            pytest.mark.jira,
            pytest.mark.project_management,
        ],
        id=f"{CredentialTypes.JIRA}_server",
    ),
    pytest.param(
        CredentialTypes.JIRA,
        CredentialsManager.jira_cloud_credentials(),
        marks=[
            pytest.mark.jira,
            pytest.mark.jira_cloud,
            pytest.mark.project_management,
        ],
        id=f"{CredentialTypes.JIRA}_cloud",
    ),
    pytest.param(
        CredentialTypes.SQL,
        CredentialsManager.sql_credentials(DataBaseDialect.POSTGRES),
        marks=pytest.mark.sql,
        id=DataBaseDialect.POSTGRES,
    ),
    pytest.param(
        CredentialTypes.SQL,
        CredentialsManager.sql_credentials(DataBaseDialect.MY_SQL),
        marks=pytest.mark.sql,
        id=DataBaseDialect.MY_SQL,
    ),
    pytest.param(
        CredentialTypes.ELASTIC,
        CredentialsManager.elasticsearch_credentials(),
        marks=pytest.mark.elastic,
        id=CredentialTypes.ELASTIC,
    ),
    pytest.param(
        CredentialTypes.MCP,
        CredentialsManager.mcp_credentials(),
        marks=pytest.mark.mcp,
        id=CredentialTypes.MCP,
    ),
    pytest.param(
        CredentialTypes.AZURE_DEVOPS,
        CredentialsManager.azure_devops_credentials(),
        marks=pytest.mark.azure,
        id=CredentialTypes.AZURE_DEVOPS,
    ),
    pytest.param(
        CredentialTypes.FILESYSTEM,
        CredentialsManager.file_system_credentials(),
        marks=pytest.mark.file_system,
        id=CredentialTypes.FILESYSTEM,
    ),
    pytest.param(
        CredentialTypes.EMAIL,
        CredentialsManager.gmail_credentials(),
        marks=[
            pytest.mark.notification,
            pytest.mark.email,
        ],
        id=CredentialTypes.EMAIL,
    ),
    pytest.param(
        CredentialTypes.TELEGRAM,
        CredentialsManager.telegram_credentials(),
        marks=[
            pytest.mark.notification,
            pytest.mark.telegram,
        ],
        id=CredentialTypes.TELEGRAM,
    ),
    pytest.param(
        CredentialTypes.SERVICE_NOW,
        CredentialsManager.servicenow_credentials(),
        marks=pytest.mark.servicenow,
        id=CredentialTypes.SERVICE_NOW,
    ),
    pytest.param(
        CredentialTypes.KEYCLOAK,
        CredentialsManager.keycloak_credentials(),
        marks=pytest.mark.keycloak,
        id=CredentialTypes.KEYCLOAK,
    ),
    pytest.param(
        CredentialTypes.KUBERNETES,
        CredentialsManager.kubernetes_credentials(),
        marks=[
            pytest.mark.kubernetes,
            pytest.mark.cloud,
            pytest.mark.skipif(
                EnvironmentResolver.is_azure(),
                reason="Still have an issue with encoding long strings",
            ),
        ],
        id=CredentialTypes.KUBERNETES,
    ),
    pytest.param(
        CredentialTypes.REPORT_PORTAL,
        CredentialsManager.report_portal_credentials(),
        marks=pytest.mark.report_portal,
        id=CredentialTypes.REPORT_PORTAL,
    ),
]

testable_integrations = [
    pytest.param(
        CredentialTypes.AWS,
        CredentialsManager.aws_credentials(),
        marks=[
            pytest.mark.aws,
            pytest.mark.cloud,
        ],
        id=CredentialTypes.AWS,
    ),
    pytest.param(
        CredentialTypes.AZURE,
        CredentialsManager.azure_credentials(),
        marks=[
            pytest.mark.azure,
            pytest.mark.cloud,
        ],
        id=CredentialTypes.AZURE,
    ),
    pytest.param(
        CredentialTypes.GCP,
        CredentialsManager.gcp_credentials(),
        marks=[
            pytest.mark.gcp,
            pytest.mark.cloud,
            pytest.mark.skipif(
                EnvironmentResolver.is_azure(),
                reason="Still have an issue with encoding long strings",
            ),
        ],
        id=CredentialTypes.GCP,
    ),
    pytest.param(
        CredentialTypes.SONAR,
        CredentialsManager.sonar_credentials(),
        marks=pytest.mark.sonar,
        id=f"{CredentialTypes.SONAR}_server",
    ),
    pytest.param(
        CredentialTypes.SONAR,
        CredentialsManager.sonar_cloud_credentials(),
        marks=pytest.mark.sonar,
        id=f"{CredentialTypes.SONAR}_cloud",
    ),
    pytest.param(
        CredentialTypes.CONFLUENCE,
        CredentialsManager.confluence_credentials(),
        marks=[
            pytest.mark.confluence,
            pytest.mark.project_management,
        ],
        id=f"{CredentialTypes.CONFLUENCE}_server",
    ),
    pytest.param(
        CredentialTypes.CONFLUENCE,
        CredentialsManager.confluence_cloud_credentials(),
        marks=[
            pytest.mark.confluence,
            pytest.mark.confluence_cloud,
            pytest.mark.project_management,
        ],
        id=f"{CredentialTypes.CONFLUENCE}_cloud",
    ),
    pytest.param(
        CredentialTypes.JIRA,
        CredentialsManager.jira_credentials(),
        marks=[
            pytest.mark.jira,
            pytest.mark.project_management,
        ],
        id=f"{CredentialTypes.JIRA}_server",
    ),
    pytest.param(
        CredentialTypes.JIRA,
        CredentialsManager.jira_cloud_credentials(),
        marks=[
            pytest.mark.jira,
            pytest.mark.jira_cloud,
            pytest.mark.project_management,
        ],
        id=f"{CredentialTypes.JIRA}_cloud",
    ),
    pytest.param(
        CredentialTypes.EMAIL,
        CredentialsManager.gmail_credentials(),
        marks=[
            pytest.mark.email,
            pytest.mark.notification,
            pytest.mark.skipif(
                EnvironmentResolver.is_localhost(),
                reason="Skipping this test on local environment",
            ),
        ],
        id=CredentialTypes.EMAIL,
    ),
    pytest.param(
        CredentialTypes.SERVICE_NOW,
        CredentialsManager.servicenow_credentials(),
        marks=pytest.mark.servicenow,
        id=CredentialTypes.SERVICE_NOW,
    ),
    pytest.param(
        CredentialTypes.KUBERNETES,
        CredentialsManager.kubernetes_credentials(),
        marks=[
            pytest.mark.kubernetes,
            pytest.mark.cloud,
            pytest.mark.skipif(
                EnvironmentResolver.is_azure(),
                reason="Still have an issue with encoding long strings",
            ),
        ],
        id=CredentialTypes.KUBERNETES,
    ),
    pytest.param(
        CredentialTypes.REPORT_PORTAL,
        CredentialsManager.report_portal_credentials(),
        marks=pytest.mark.report_portal,
        id=CredentialTypes.REPORT_PORTAL,
    ),
]

invalid_integrations = [
    pytest.param(
        CredentialTypes.AWS,
        CredentialsManager.invalid_aws_credentials(),
        "An error occurred (SignatureDoesNotMatch) when calling the GetUser operation: The request signature we calculated does not match the signature you provided. Check your AWS Secret Access Key and signing method. Consult the service documentation for details.",
        marks=[
            pytest.mark.aws,
            pytest.mark.cloud,
        ],
        id=CredentialTypes.AWS,
    ),
    pytest.param(
        CredentialTypes.AZURE,
        CredentialsManager.invalid_azure_credentials(),
        "Invalid client secret provided. Ensure the secret being sent in the request is the client secret value, not the client secret ID, for a secret added to app",
        marks=[
            pytest.mark.azure,
            pytest.mark.cloud,
        ],
        id=CredentialTypes.AZURE,
    ),
    pytest.param(
        CredentialTypes.GCP,
        CredentialsManager.invalid_gcp_credentials(),
        "Error: ('Could not deserialize key data. The data may be in an incorrect format, "
        + "the provided password may be incorrect, it may be encrypted with an unsupported algorithm, "
        + "or it may be an unsupported key type",
        marks=[
            pytest.mark.gcp,
            pytest.mark.cloud,
            pytest.mark.skipif(
                EnvironmentResolver.is_azure(),
                reason="Still have an issue with encoding long strings",
            ),
        ],
        id=CredentialTypes.GCP,
    ),
    pytest.param(
        CredentialTypes.SONAR,
        CredentialsManager.invalid_sonar_credentials(),
        "Invalid token",
        marks=pytest.mark.sonar,
        id=f"{CredentialTypes.SONAR}_server",
    ),
    pytest.param(
        CredentialTypes.SONAR,
        CredentialsManager.invalid_sonar_cloud_credentials(),
        "Invalid token",
        marks=pytest.mark.sonar,
        id=f"{CredentialTypes.SONAR}_cloud",
    ),
    pytest.param(
        CredentialTypes.EMAIL,
        CredentialsManager.invalid_gmail_credentials(),
        "SMTP Code: 535, Message: 5.7.8 Username and Password not accepted.",
        marks=[
            pytest.mark.email,
            pytest.mark.notification,
            pytest.mark.skipif(
                EnvironmentResolver.is_localhost(),
                reason="Skipping this test on local environment",
            ),
        ],
        id=CredentialTypes.EMAIL,
    ),
    pytest.param(
        CredentialTypes.JIRA,
        CredentialsManager.invalid_jira_credentials(),
        "Unauthorized (401)",
        marks=pytest.mark.jira,
        id=CredentialTypes.JIRA,
    ),
    pytest.param(
        CredentialTypes.CONFLUENCE,
        CredentialsManager.invalid_confluence_credentials(),
        "Access denied",
        marks=pytest.mark.confluence,
        id=CredentialTypes.CONFLUENCE,
    ),
    pytest.param(
        CredentialTypes.SERVICE_NOW,
        CredentialsManager.invalid_servicenow_credentials(),
        'ServiceNow tool exception. Status: 401. Response: {"error":{"message":"User Not Authenticated","detail":"Required to provide Auth information"}',
        marks=pytest.mark.servicenow,
        id=CredentialTypes.SERVICE_NOW,
    ),
    pytest.param(
        CredentialTypes.KUBERNETES,
        CredentialsManager.invalid_kubernetes_credentials(),
        "Error: (401)\nReason: Unauthorized",
        marks=[
            pytest.mark.kubernetes,
            pytest.mark.cloud,
        ],
        id=CredentialTypes.KUBERNETES,
    ),
    pytest.param(
        CredentialTypes.REPORT_PORTAL,
        CredentialsManager.invalid_report_portal_credentials(),
        "401 Client Error:  for url: https://report-portal.core.kuberocketci.io/api/v1/epm-cdme/launch?page.page=1",
        marks=pytest.mark.report_portal,
        id=CredentialTypes.REPORT_PORTAL,
    ),
]

empty_credentials_integrations = [
    pytest.param(
        [
            CredentialValues(key="url", value="https://gitlab.com"),
        ],
        CredentialTypes.GIT,
        Toolkit.VCS,
        VcsTool.GITLAB,
        f"Using gitlab tool get info about MR №7014 for repo with id '{CredentialsManager.get_parameter('GITLAB_PROJECT_ID')}'",
        """
            It seems there is an issue with the GitLab configuration, as it hasn't been set up properly for this tool.
            This requires setting up authentication and configuration to connect to a GitLab instance.
    
            Could you please check your GitLab tool configuration and provide the necessary access details so that I can assist you further?
        """,
        marks=[pytest.mark.gitlab],
        id=f"{CredentialTypes.GIT}_gitlab_empty",
    ),
    pytest.param(
        [
            CredentialValues(key="url", value="https://github.com"),
        ],
        CredentialTypes.GIT,
        Toolkit.VCS,
        VcsTool.GITHUB,
        f"Using github tool get info about issue №5 for the repo {CredentialsManager.get_parameter('GITHUB_PROJECT')}.",
        """
            It seems there is an issue with accessing the GitHub API due to a missing configuration.
            Unfortunately, I can't fetch the information directly at the moment.
            However, you can access information about an issue using the following steps on your own:
            
            1. Navigate to the Issues tab of the repository [wild47/final_task](https://github.com/wild47/final_task).
            2. Look for issue number 5 or directly visit `https://github.com/wild47/final_task/issues/5`,
            and it should display all the details regarding that specific issue.
            
            If there's anything else you'd like assistance with, please let me know!
        """,
        marks=[pytest.mark.github],
        id=f"{CredentialTypes.GIT}_github_empty",
    ),
    pytest.param(
        [
            CredentialValues(key="url", value=CredentialsManager.AUTO_GENERATED),
        ],
        CredentialTypes.EMAIL,
        Toolkit.NOTIFICATION,
        NotificationTool.EMAIL,
        EMAIL_TOOL_PROMPT,
        """
            It looks like there's an issue with the SMTP configuration; it's missing a valid SMTP URL to send the email.
            Please ensure that the SMTP settings are properly configured in the system.
            If you have access to the SMTP details, such as the server URL, username, and password, you could input them into the system to resolve this issue.
        """,
        marks=[pytest.mark.email, pytest.mark.notification],
        id=f"{CredentialTypes.EMAIL}_empty",
    ),
    pytest.param(
        [
            CredentialValues(key="url", value=CredentialsManager.AUTO_GENERATED),
        ],
        CredentialTypes.TELEGRAM,
        Toolkit.NOTIFICATION,
        NotificationTool.TELEGRAM,
        TELEGRAM_TOOL_PROMPT,
        """
            It seems I don't have access to the necessary Telegram bot token to send a message. 
            
            You should verify that the bot token is set up correctly or send the message directly through your Telegram bot using your bot's token. 
            
            If you have your bot token and need help with the API request, let me know!
        """,
        marks=[pytest.mark.telegram, pytest.mark.notification],
        id=f"{CredentialTypes.TELEGRAM}_empty",
    ),
    pytest.param(
        [
            CredentialValues(
                key="url", value=CredentialsManager.get_parameter("JIRA_URL")
            )
        ],
        CredentialTypes.JIRA,
        Toolkit.PROJECT_MANAGEMENT,
        ProjectManagementTool.JIRA,
        JIRA_TOOL_PROMPT,
        """
            It seems that there's an authorization issue when trying to access the JIRA ticket.
            The error indicates that the request is unauthorized.
            You may need to ensure that the correct credentials are being used, or check if you have the necessary permissions to access the ticket.
            
            If there's anything else you'd like to try or if you have further details, let me know!
        """,
        marks=[pytest.mark.jira, pytest.mark.project_management],
        id=f"{CredentialTypes.JIRA}_empty",
    ),
    pytest.param(
        [],
        CredentialTypes.CONFLUENCE,
        Toolkit.PROJECT_MANAGEMENT,
        ProjectManagementTool.CONFLUENCE,
        CONFLUENCE_TOOL_PROMPT,
        """
            It looks like I don't have the required Confluence URL and credentials set up to perform the requested action.
            If you have access to Confluence, please provide these details or try to access the page directly through your Confluence account.
        """,
        marks=[pytest.mark.confluence, pytest.mark.project_management],
        id=f"{CredentialTypes.CONFLUENCE}_empty",
    ),
    pytest.param(
        [
            CredentialValues(key="url", value=""),
        ],
        CredentialTypes.SERVICE_NOW,
        Toolkit.SERVICENOW,
        ServiceNowTool.SERVICE_NOW,
        PROMPT,
        """
            It appears that the ServiceNow configuration is not set, which prevents me from executing the request.
            Please ensure that the ServiceNow configuration, including necessary authentication details,
            is properly set up before using the ServiceNow tool. If you have access to configure these details, please do so and try again.
        """,
        marks=[pytest.mark.servicenow],
        id=f"{CredentialTypes.SERVICE_NOW}_empty",
    ),
    pytest.param(
        [
            CredentialValues(key="url", value=CredentialsManager.AUTO_GENERATED),
        ],
        CredentialTypes.OPENAPI,
        Toolkit.OPEN_API,
        OpenApiTool.GET_OPEN_API_SPEC,
        OPEN_API_SPEC_TOOL_TASK,
        """
            It seems that I don't have access to the OpenAPI specification for the `/v1/assistants` endpoint right now.
            To help you better, could you please provide more details about what you'd like to know regarding this endpoint?
            Are you looking for information on request parameters, expected responses, authentication, or something else?
        """,
        marks=[pytest.mark.openapi],
        id=f"{CredentialTypes.OPENAPI}_empty",
    ),
]
