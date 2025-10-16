import os

import pytest

from codemie_test_harness.tests.enums.tools import Toolkit, PluginTool
from codemie_test_harness.tests.test_data.plugin_tools_test_data import (
    list_files_plugin_tools_test_data,
    CREATE_READ_DELETE_FILE_TEST_DATA,
)
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_tool_triggered,
)
from codemie_test_harness.tests.utils.constants import TESTS_PATH


@pytest.mark.assistant
@pytest.mark.plugin
@pytest.mark.api
@pytest.mark.parametrize(
    "prompt,expected_response,tool_name",
    list_files_plugin_tools_test_data,
    ids=[row[2] for row in list_files_plugin_tools_test_data],
)
def test_assistant_with_list_files_plugin_tools(
    development_plugin,
    assistant_utils,
    assistant,
    integration_utils,
    similarity_check,
    prompt,
    expected_response,
    tool_name,
):
    assistant = assistant(Toolkit.PLUGIN, Toolkit.PLUGIN, settings=development_plugin)

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, prompt, minimal_response=False
    )

    assert_tool_triggered(tool_name, triggered_tools)

    similarity_check.check_similarity(response, expected_response)


@pytest.mark.assistant
@pytest.mark.plugin
@pytest.mark.api
@pytest.mark.plugin
def test_assistant_with_modify_files_plugin_tools(
    assistant_utils,
    assistant,
    development_plugin,
    similarity_check,
):
    file_name = get_random_name()
    try:
        assistant = assistant(
            Toolkit.PLUGIN, Toolkit.PLUGIN, settings=development_plugin
        )

        response, triggered_tools = assistant_utils.ask_assistant(
            assistant,
            CREATE_READ_DELETE_FILE_TEST_DATA["create_file_prompt"].format(
                file_name, file_name
            ),
            minimal_response=False,
        )

        assert_tool_triggered(PluginTool.WRITE_FILE_TO_FILE_SYSTEM, triggered_tools)

        similarity_check.check_similarity(
            response,
            CREATE_READ_DELETE_FILE_TEST_DATA["create_file_response"].format(
                file_name, file_name
            ),
        )

        response, triggered_tools = assistant_utils.ask_assistant(
            assistant,
            CREATE_READ_DELETE_FILE_TEST_DATA["git_command_prompt"].format(file_name),
            minimal_response=False,
        )
        assert_tool_triggered(PluginTool.GENERIC_GIT_TOOL, triggered_tools)

        similarity_check.check_similarity(
            response,
            CREATE_READ_DELETE_FILE_TEST_DATA["git_command_response"].format(file_name),
        )

        response, triggered_tools = assistant_utils.ask_assistant(
            assistant,
            CREATE_READ_DELETE_FILE_TEST_DATA["show_file_content_prompt"].format(
                file_name
            ),
            minimal_response=False,
        )

        assert_tool_triggered(PluginTool.READ_FILE_FROM_FILE_SYSTEM, triggered_tools)

        similarity_check.check_similarity(
            response,
            CREATE_READ_DELETE_FILE_TEST_DATA["show_file_content_response"].format(
                file_name
            ),
        )
    finally:
        os.remove(f"{str(TESTS_PATH / file_name)}.properties")
