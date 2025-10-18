import pytest
from hamcrest import assert_that, equal_to

from codemie_sdk.models.integration import CredentialTypes
from codemie_test_harness.tests.enums.tools import Toolkit, NotificationTool
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.enums.environment import Environment
from codemie_test_harness.tests.utils.env_resolver import get_environment
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered
from codemie_test_harness.tests.test_data.notification_tools_test_data import (
    EMAIL_TOOL_PROMPT,
    EMAIL_RESPONSE,
    EMAIL_SUBJECT,
    EMAIL_BODY,
    TELEGRAM_TOOL_PROMPT,
    TELEGRAM_RESPONSE,
)


@pytest.mark.assistant
@pytest.mark.notification
@pytest.mark.email
@pytest.mark.api
@pytest.mark.skipif(
    get_environment() in [Environment.LOCALHOST, Environment.GCP],
    reason="Skipping this test on local environment",
)
def test_assistant_with_email_tool(
    assistant,
    assistant_utils,
    similarity_check,
    integration_utils,
    gmail_message_operator,
):
    credential_values = CredentialsManager.gmail_credentials()
    settings = integration_utils.create_integration(
        CredentialTypes.EMAIL, credential_values
    )

    assistant = assistant(
        Toolkit.NOTIFICATION, NotificationTool.EMAIL, settings=settings
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, EMAIL_TOOL_PROMPT, minimal_response=False
    )
    assert_tool_triggered(NotificationTool.EMAIL, triggered_tools)
    similarity_check.check_similarity(response, EMAIL_RESPONSE)

    message_data = gmail_message_operator.get_messages_list()
    latest_message_id = message_data["messages"][0]["id"]
    message_content = gmail_message_operator.get_specific_message_content(
        latest_message_id
    )

    message_body = message_content["snippet"]
    message_title = next(
        (
            header["value"]
            for header in message_content["payload"]["headers"]
            if header["name"].lower() == "subject"
        )
    )

    assert_that(message_body, equal_to(EMAIL_BODY))
    assert_that(message_title, equal_to(EMAIL_SUBJECT))


@pytest.mark.assistant
@pytest.mark.notification
@pytest.mark.telegram
@pytest.mark.api
def test_assistant_with_telegram_tool(
    assistant, assistant_utils, similarity_check, integration_utils
):
    credential_values = CredentialsManager.telegram_credentials()
    settings = integration_utils.create_integration(
        CredentialTypes.TELEGRAM, credential_values
    )

    assistant = assistant(
        Toolkit.NOTIFICATION, NotificationTool.TELEGRAM, settings=settings
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, TELEGRAM_TOOL_PROMPT, minimal_response=False
    )
    assert_tool_triggered(NotificationTool.TELEGRAM, triggered_tools)
    similarity_check.check_similarity(response, TELEGRAM_RESPONSE)
