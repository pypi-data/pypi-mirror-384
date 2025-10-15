import pytest

from codemie_test_harness.tests.enums.tools import (
    McpServerTime,
    CliMcpServer,
    McpServerFetch,
)
from codemie_test_harness.tests.test_data.mcp_server_test_data import (
    FETCH_MCP_SERVER,
    fetch_expected_response,
    time_expected_response,
    TIME_MCP_SERVER_WITH_CONFIG,
    time_server_prompt,
    fetch_server_prompt,
)
from codemie_test_harness.tests.test_data.mcp_server_test_data import (
    cli_mcp_server_test_data,
    CLI_MCP_SERVER,
)
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.mcp
@pytest.mark.api
def test_workflow_with_assistant_with_time_mcp_server(
    assistant,
    workflow_with_assistant,
    workflow_utils,
    similarity_check,
):
    """Test workflow execution with Time MCP server."""
    assistant = assistant(mcp_server=TIME_MCP_SERVER_WITH_CONFIG)

    workflow_with_assistant = workflow_with_assistant(assistant, time_server_prompt)
    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(McpServerTime.CONVERT_TIME, triggered_tools)

    similarity_check.check_similarity(response, time_expected_response)


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.mcp
@pytest.mark.api
@pytest.mark.parametrize(
    "command, expected_answer",
    cli_mcp_server_test_data,
    ids=[f"{row[0]}" for row in cli_mcp_server_test_data],
)
def test_workflow_with_assistant_with_cli_mcp_server(
    assistant,
    workflow_with_assistant,
    workflow_utils,
    similarity_check,
    command,
    expected_answer,
):
    """Test workflow execution with CLI MCP server."""
    assistant = assistant(mcp_server=CLI_MCP_SERVER)

    workflow_with_assistant = workflow_with_assistant(
        assistant,
        "Run command. In case of error just explain the issue and do not suggest any workarounds and do not try to run command with other parameters.",
    )
    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name, f"execute the command: '{command}'"
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(CliMcpServer.RUN_COMMAND, triggered_tools)

    similarity_check.check_similarity(response, expected_answer)


@pytest.mark.workflow
@pytest.mark.workflow_with_assistant
@pytest.mark.mcp
@pytest.mark.api
def test_workflow_with_assistant_with_fetch_mcp_server(
    assistant,
    workflow_with_assistant,
    workflow_utils,
    similarity_check,
):
    """Test workflow execution with Fetch MCP server."""
    assistant = assistant(mcp_server=FETCH_MCP_SERVER)

    workflow_with_assistant = workflow_with_assistant(assistant, fetch_server_prompt)
    response = workflow_utils.execute_workflow(
        workflow_with_assistant.id, assistant.name
    )

    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_with_assistant
    )
    assert_tool_triggered(McpServerFetch.FETCH, triggered_tools)

    similarity_check.check_similarity(response, fetch_expected_response)
