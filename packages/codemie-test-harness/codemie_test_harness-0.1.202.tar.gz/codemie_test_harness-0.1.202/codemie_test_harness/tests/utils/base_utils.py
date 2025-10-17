import json
import random
import re
import string
import time
import unicodedata
from time import sleep

from hamcrest import assert_that, equal_to, contains_string

from codemie_sdk import CodeMieClient
from codemie_sdk.exceptions import ApiError
from codemie_sdk.models.workflow_state import (
    WorkflowExecutionState,
    WorkflowExecutionStatusEnum,
)
from codemie_sdk.services.workflow_execution_state import (
    WorkflowExecutionStateService,
)
from codemie_test_harness.tests import autotest_entity_prefix
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager


class BaseUtils:
    def __init__(self, client: CodeMieClient):
        self.client = client


def get_random_name():
    """Generate a random name with lowercase letters and underscores only, and cannot begin with '_' or '-'."""
    characters = string.ascii_lowercase
    random_string = "".join(random.choice(characters) for _ in range(15))
    # Generate the remaining characters
    random_name = f"{autotest_entity_prefix}{random_string}"
    return random_name


def to_camel_case(input_string):
    # Remove non-letter characters
    cleaned = re.sub(r"[^a-zA-Z]", " ", input_string)
    # Split into words
    words = cleaned.split()
    # Convert to camelCase
    camel_case = words[0].capitalize() + "".join(
        word.capitalize() for word in words[1:]
    )
    return camel_case


def wait_for_completion(
    execution_state_service: WorkflowExecutionStateService,
    state_id: str,
    timeout: int = int(CredentialsManager.get_parameter("DEFAULT_TIMEOUT", "120")),
    pool_interval: int = 3,
) -> WorkflowExecutionState:
    start_time = time.time()
    while time.time() - start_time < timeout:
        states = [row for row in execution_state_service.list() if row.id == state_id]
        if len(states) == 0:
            sleep(pool_interval)
            continue
        state = states[0]
        if state.status == WorkflowExecutionStatusEnum.SUCCEEDED:
            return state
        elif state.status == WorkflowExecutionStatusEnum.FAILED:
            raise ApiError(
                f"State execution failed: {execution_state_service.get_output(state_id)}"
            )
        sleep(pool_interval)
    raise TimeoutError("State was not executed within the timeout period.")


def clean_json(json_str):
    try:
        # Attempt to parse the JSON string directly
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract embedded JSON from Markdown-like syntax
        pattern = re.compile(
            r'(\{(?:[^{}"]|"(?:[^"\\]|\\.)*")*\}|\[(?:[^\[\]"]|"(?:[^"\\]|\\.)*")*\])'
        )

        matcher = pattern.search(json_str)

        if matcher:
            unwrapped_json_str = matcher.group(1)
            # Replace non-breaking spaces with regular spaces and remove control characters
            unwrapped_json_str = unwrapped_json_str.replace("\u00a0", " ")
            unwrapped_json_str = "".join(
                c
                for c in unwrapped_json_str
                if not (unicodedata.category(c) == "Cc" and c not in "\r\n\t")
            )
            try:
                return json.loads(unwrapped_json_str)
            except json.JSONDecodeError as inner_exception:
                raise ValueError("Invalid JSON string") from inner_exception
        else:
            raise ValueError("No JSON found in the Markdown string")


def percent_of_relevant_titles(response):
    """
    Calculate the percentage of relevant titles in a response.
    Usage:
        percent = percent_of_relevant_titles(response)
    """
    json_to_parse = clean_json(response)
    search_terms = [
        "ai",
        "artificial intelligence",
        "machine learning",
        "natural language",
    ]
    percent = (
        sum(
            1
            for item in json_to_parse
            if any(term in item.get("title", "").lower() for term in search_terms)
        )
        * 10
    )
    return percent


def wait_for_entity(get_entity_callable, entity_name, timeout=10, poll_interval=3):
    """
    Waits for an entity to be created or available with a timeout.
    :param entity_name: Entity name
    :param get_entity_callable: A callable that attempts to retrieve the entity.
                                Should raise NotFoundError if the entity is not found.
    :param timeout: The maximum time to wait for the entity (in seconds).
    :param poll_interval: The time between consecutive checks (in seconds).
    :return: The entity object if it is successfully retrieved.
    :raises TimeoutError: If the entity is not found within the timeout period.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            entities = [raw for raw in get_entity_callable() if raw.name == entity_name]
        except AttributeError:
            entities = [
                raw for raw in get_entity_callable() if raw.alias == entity_name
            ]
        if len(entities) > 0:
            return entities[0]
        time.sleep(poll_interval)

    # If timeout is reached and entity is not found, raise an error
    raise TimeoutError("Entity was not found within the timeout period.")


def assert_response(response, status_code, message=None):
    assert_that(response.status_code, equal_to(status_code))
    if message:
        error_details = json.loads(response.content)["error"]["details"]
        if isinstance(error_details, list):
            assert_that(error_details[0]["msg"], equal_to(message))
        else:
            assert_that(error_details, equal_to(message))


def assert_error_details(response, status_code, message):
    assert_that(
        response.status_code, equal_to(status_code), "Status code is not expected."
    )
    error_details = json.loads(response.content)["error"]["details"]
    assert_that(
        error_details, contains_string(message), "Error message is not expected."
    )


def credentials_to_dict(credentials):
    return {cred.key: cred.value for cred in credentials}


def assert_tool_triggered(tool_name, triggered_tools):
    """
    Assert that the expected tool(s) were triggered during assistant interaction.

    Args:
        tool_name: Either a single tool enum or a tuple of tool enums that should be triggered
        triggered_tools: List of tools that were actually triggered

    Raises:
        AssertionError: If any of the expected tools were not found in triggered_tools
                       (for tuples, ALL tools must be present)
    """
    # Handle both single tools and tuples of tools
    if isinstance(tool_name, tuple):
        tools_to_check = tool_name
    else:
        tools_to_check = (tool_name,)

    # Check each expected tool
    found_tools = []
    missing_tools = []

    for tool in tools_to_check:
        tool_value_lower = tool.value.lower()
        tool_value_with_spaces = tool.value.replace("_", " ").lower()

        # Check if this specific tool was triggered
        tool_found = False
        for triggered_tool in triggered_tools:
            if (
                triggered_tool.lower() == tool_value_lower
                or triggered_tool.lower() == tool_value_with_spaces
                or tool_value_with_spaces in triggered_tool.lower()
            ):
                found_tools.append(tool.value)
                tool_found = True
                break

        if not tool_found:
            missing_tools.append(tool.value)

    # Assert that ALL expected tools were found
    if missing_tools:
        expected_tools = [tool.value for tool in tools_to_check]

        if len(tools_to_check) == 1:
            assert False, (
                f"Tool validation failed:\n"
                f"Expected tool '{expected_tools[0]}' to be triggered\n"
                f"But it was not found in triggered tools: {triggered_tools}\n"
            )
        else:
            assert False, (
                f"Tool validation failed:\n"
                f"Expected ALL of these tools to be triggered: {expected_tools}\n"
                f"Missing tools: {missing_tools}\n"
                f"Found tools: {found_tools}\n"
                f"Actually triggered: {triggered_tools}\n"
            )
