from codemie_test_harness.tests.utils.env_resolver import EnvironmentResolver
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered

import pytest

from codemie_test_harness.tests.enums.tools import Toolkit
from codemie_test_harness.tests.test_data.open_api_tools_test_data import (
    open_api_tools_test_data,
)


@pytest.mark.assistant
@pytest.mark.openapi
@pytest.mark.api
@pytest.mark.testcase("EPMCDME-6127")
@pytest.mark.skipif(
    EnvironmentResolver.is_azure(),
    reason="Still have an issue with encoding long strings",
)
@pytest.mark.parametrize(
    "tool_name,prompt,expected_response",
    open_api_tools_test_data,
    ids=[f"{row[0]}" for row in open_api_tools_test_data],
)
def test_create_assistant_with_open_api_tool(
    assistant_utils,
    assistant,
    similarity_check,
    open_api_integration,
    tool_name,
    prompt,
    expected_response,
):
    assistant_instance = assistant(
        Toolkit.OPEN_API, tool_name, settings=open_api_integration
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant_instance, prompt, minimal_response=False
    )

    assert_tool_triggered(tool_name, triggered_tools)
    similarity_check.check_similarity(response, expected_response)
