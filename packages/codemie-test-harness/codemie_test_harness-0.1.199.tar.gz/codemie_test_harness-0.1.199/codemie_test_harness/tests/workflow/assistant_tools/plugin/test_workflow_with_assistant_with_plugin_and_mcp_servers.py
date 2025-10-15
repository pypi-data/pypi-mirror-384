import os

import pytest

from codemie_test_harness.tests.enums.tools import Toolkit, CliMcpServer, PluginTool
from codemie_test_harness.tests.test_data.mcp_server_test_data import (
    cli_mcp_server_with_plugin_test_data,
    filesystem_mcp_server_with_plugin_test_data,
)
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered
from codemie_test_harness.tests.utils.constants import TESTS_PATH


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.plugin
@pytest.mark.mcp
@pytest.mark.api
@pytest.mark.parametrize(
    "prompt,expected_response",
    cli_mcp_server_with_plugin_test_data,
    ids=[f"{row[0]}" for row in cli_mcp_server_with_plugin_test_data],
)
def test_workflow_with_assistant_with_plugin_and_cli_mcp_server(
    cli_server,
    assistant,
    workflow_utils,
    workflow_with_assistant,
    similarity_check,
    prompt,
    expected_response,
):
    assistant = assistant(Toolkit.PLUGIN, Toolkit.PLUGIN, settings=cli_server)

    workflow_with_assistant = workflow_with_assistant(assistant, "Run tool")
    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name, user_input=prompt
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(CliMcpServer.RUN_COMMAND, triggered_tools)

    similarity_check.check_similarity(response, expected_response)


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.plugin
@pytest.mark.mcp
@pytest.mark.api
@pytest.mark.parametrize(
    "prompt,expected_response,tool_name",
    filesystem_mcp_server_with_plugin_test_data,
    ids=[f"{row[2]}" for row in filesystem_mcp_server_with_plugin_test_data],
)
def test_workflow_with_assistant_with_plugin_and_filesystem_mcp_server(
    filesystem_server,
    assistant,
    workflow_utils,
    workflow_with_assistant,
    similarity_check,
    prompt,
    expected_response,
    tool_name,
):
    try:
        assistant = assistant(
            Toolkit.PLUGIN, Toolkit.PLUGIN, settings=filesystem_server
        )

        workflow_with_assistant = workflow_with_assistant(assistant, "Run tool")
        response = workflow_utils.execute_workflow(
            workflow_with_assistant.id, assistant.name, user_input=prompt
        )

        triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
            workflow_with_assistant
        )
        # Match the pattern from assistant test - conditionally assert tools
        if tool_name != PluginTool.READ_FILE:
            assert_tool_triggered(tool_name, triggered_tools)

        similarity_check.check_similarity(response, expected_response)
    finally:
        file_to_remove = f"{str(TESTS_PATH / 'sdk_tests')}.properties"
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)
