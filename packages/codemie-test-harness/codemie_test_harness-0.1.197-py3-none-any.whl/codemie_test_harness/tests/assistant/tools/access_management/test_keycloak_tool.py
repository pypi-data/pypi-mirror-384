import pytest

from codemie_test_harness.tests.enums.tools import Toolkit, AccessManagementTool
from codemie_test_harness.tests.test_data.keycloak_tool_test_data import (
    KEYCLOAK_TOOL_PROMPT,
    KEYCLOAK_TOOL_RESPONSE,
)
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


@pytest.mark.assistant
@pytest.mark.keycloak
@pytest.mark.api
def test_assistant_with_keycloak_tool(
    assistant_utils,
    assistant,
    keycloak_integration,
    similarity_check,
):
    keycloak_assistant = assistant(
        Toolkit.ACCESS_MANAGEMENT,
        AccessManagementTool.KEYCLOAK,
        settings=keycloak_integration,
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        keycloak_assistant, KEYCLOAK_TOOL_PROMPT, minimal_response=False
    )

    assert_tool_triggered(AccessManagementTool.KEYCLOAK, triggered_tools)

    similarity_check.check_similarity(response, KEYCLOAK_TOOL_RESPONSE)
