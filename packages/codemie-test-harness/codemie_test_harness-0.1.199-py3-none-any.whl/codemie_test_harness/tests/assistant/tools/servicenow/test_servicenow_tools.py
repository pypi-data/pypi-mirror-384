import pytest

from codemie_test_harness.tests.enums.tools import Toolkit, ServiceNowTool
from codemie_test_harness.tests.test_data.servicenow_tools_test_data import (
    PROMPT,
    EXPECTED_RESPONSE,
)
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


@pytest.mark.assistant
@pytest.mark.servicenow
@pytest.mark.api
def test_assistant_with_servicenow_tools(
    assistant_utils,
    assistant,
    service_now_integration,
    similarity_check,
):
    servicenow_assistant = assistant(
        Toolkit.SERVICENOW, ServiceNowTool.SERVICE_NOW, settings=service_now_integration
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        servicenow_assistant, PROMPT, minimal_response=False
    )

    assert_tool_triggered(ServiceNowTool.SERVICE_NOW, triggered_tools)
    similarity_check.check_similarity(response, EXPECTED_RESPONSE, 80)
