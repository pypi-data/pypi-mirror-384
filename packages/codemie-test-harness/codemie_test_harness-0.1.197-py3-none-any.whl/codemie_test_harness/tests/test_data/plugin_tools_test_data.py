from codemie_test_harness.tests.enums.tools import PluginTool
from codemie_test_harness.tests.utils.constants import TESTS_PATH

list_files_plugin_tools_test_data = [
    (
        f"list files in the {TESTS_PATH} directory",
        f"""
            Here is a list of files and directories in `{TESTS_PATH}`:

            - Files:
              - `.DS_Store`
              - `__init__.py`
              - `conftest.py`

            - Directories:
              - `__pycache__`
              - `assistant`
              - `e2e`
              - `enums`
              - `integrations`
              - `llm`
              - `providers`
              - `search`
              - `service`
              - `test_data`
              - `ui`
              - `utils`
              - `workflow`
        """,
        PluginTool.LIST_FILES_IN_DIRECTORY,
    ),
    (
        "execute 'ls' command",
        f"""
            Here is a list of files and directories in `{TESTS_PATH}`:

            - Files:
              - `.DS_Store`
              - `__init__.py`
              - `conftest.py`

            - Directories:
              - `__pycache__`
              - `assistant`
              - `e2e`
              - `enums`
              - `integrations`
              - `llm`
              - `providers`
              - `search`
              - `service`
              - `test_data`
              - `ui`
              - `utils`
              - `workflow`
        """,
        PluginTool.RUN_COMMAND_LINE_TOOL,
    ),
    (
        "execute command: echo 'Test Message'. In the end return output of the command.",
        "Test Message",
        PluginTool.RUN_COMMAND_LINE_TOOL,
    ),
]

CREATE_READ_DELETE_FILE_TEST_DATA = {
    "create_file_prompt": "create a new {}.properties file with content {}=preview",
    "create_file_response": "I have successfully created the {}.properties file with the content {}=preview.",
    "git_command_prompt": "execute command: git add {}.properties and return if file was added to the staging area.",
    "git_command_response": "The file `{}.properties` has been added to the staging area.",
    "show_file_content_prompt": f"show the content of {TESTS_PATH}/{{}}.properties file",
    "show_file_content_response": "{}=preview",
    "remove_file_prompt": "execute command: git rm -f {}.properties",
    "remove_file_response": "The file `{}.properties` has been removed from the git repository.",
}

"""Test data for dual time plugin MCP server tests."""

dual_time_plugin_test_data = [
    (
        "Show tools with their name and description",
        """
            Sure, here are the tools available with their name and description:

            1. **functions._get_current_time_2f90**: 
               - **Description**: Get current time in a specific timezone. If no timezone is provided by the user, it uses 'Asia/Tokyo' as the local timezone.

            2. **functions._convert_time_2f90**: 
               - **Description**: Convert time between timezones. If no source timezone is provided by the user, it uses 'Asia/Tokyo' as the local timezone. Similarly, if no target timezone is provided, it uses 'Asia/Tokyo' as the local timezone.

            3. **functions._get_current_time_5cba**: 
               - **Description**: Similar to `_get_current_time_2f90`, this gets the current time in a specific timezone, defaulting to 'Asia/Tokyo' if no timezone is provided.

            4. **functions._convert_time_5cba**: 
               - **Description**: Similar to `_convert_time_2f90`, this converts time between timezones, defaulting to 'Asia/Tokyo' if no source or target timezone is provided. 

            These tools are designed to help manage and convert timezone-related data efficiently.
        """,
    ),
    (
        "What is the current time in Kyiv? Return in format: The current time in Kyiv (Europe/Kiev timezone) is: $time_here",
        "The current time in Kyiv (Europe/Kiev timezone) is",
    ),
    (
        "What is the current time in Tokyo? Return in format: The current time in Tokyo (Asia/Tokyo timezone) is: $time_here",
        "The current time in Tokyo (Asia/Tokyo timezone) is",
    ),
]
