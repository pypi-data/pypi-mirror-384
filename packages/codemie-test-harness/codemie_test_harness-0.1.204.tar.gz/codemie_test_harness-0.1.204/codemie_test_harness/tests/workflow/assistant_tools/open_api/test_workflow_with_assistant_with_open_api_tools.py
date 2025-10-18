from codemie_test_harness.tests.utils.env_resolver import EnvironmentResolver

import pytest

from codemie_test_harness.tests.enums.tools import Toolkit
from codemie_test_harness.tests.test_data.open_api_tools_test_data import (
    open_api_tools_test_data,
)
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.openapi
@pytest.mark.api
@pytest.mark.parametrize(
    "tool_name, prompt, expected_response",
    open_api_tools_test_data,
    ids=[f"{row[0]}" for row in open_api_tools_test_data],
)
@pytest.mark.skipif(
    EnvironmentResolver.is_azure(),
    reason="Still have an issue with encoding long strings",
)
def test_workflow_with_assistant_with_open_api_tools(
    assistant,
    workflow_with_assistant,
    open_api_integration,
    workflow_utils,
    similarity_check,
    tool_name,
    prompt,
    expected_response,
):
    assistant = assistant(Toolkit.OPEN_API, tool_name, settings=open_api_integration)

    workflow_with_assistant = workflow_with_assistant(assistant, "Run")
    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name, prompt
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(tool_name, triggered_tools)

    similarity_check.check_similarity(response, expected_response)
