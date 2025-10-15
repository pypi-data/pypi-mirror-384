"""Tests for Confluence datasource operations - Final version."""

import os
import pytest
from hamcrest import assert_that, equal_to
from requests import HTTPError

from codemie_test_harness.tests.test_data.pm_tools_test_data import (
    JIRA_TOOL_PROMPT,
    RESPONSE_FOR_JIRA_TOOL,
    JIRA_CLOUD_TOOL_PROMPT,
    RESPONSE_FOR_JIRA_CLOUD_TOOL,
)
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_response,
    assert_tool_triggered,
)
from codemie_test_harness.tests.enums.tools import Default


@pytest.fixture(scope="function")
def jira_cloud_datasource(datasource_utils, jira_cloud_integration):
    datasource = datasource_utils.create_jira_datasource(
        setting_id=jira_cloud_integration.id, jql=CredentialsManager.jira_cloud_jql()
    )
    yield datasource
    if datasource:
        datasource_utils.delete_datasource(datasource)


@pytest.mark.datasource
@pytest.mark.project_management
@pytest.mark.api
@pytest.mark.parametrize(
    "datasource_fixture, prompt, expected_response",
    [
        pytest.param(
            "jira_datasource",
            JIRA_TOOL_PROMPT,
            RESPONSE_FOR_JIRA_TOOL,
            marks=pytest.mark.jira,
            id="Jira",
        ),
        pytest.param(
            "jira_cloud_datasource",
            JIRA_CLOUD_TOOL_PROMPT,
            RESPONSE_FOR_JIRA_CLOUD_TOOL,
            marks=[pytest.mark.jira, pytest.mark.jira_cloud],
            id="Jira Cloud",
        ),
    ],
)
def test_create_datasource_with_jira_and_jira_cloud_integration(
    request,
    assistant,
    assistant_utils,
    datasource_utils,
    kb_context,
    similarity_check,
    datasource_fixture,
    prompt,
    expected_response,
):
    datasource = request.getfixturevalue(datasource_fixture)
    assistant = assistant(
        context=kb_context(datasource), system_prompt="Run tools on each user prompt"
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, prompt, minimal_response=False
    )
    assert_tool_triggered(Default.SEARCH_KB, triggered_tools)
    similarity_check.check_similarity(response, expected_response)

    datasource_utils.update_jira_datasource(
        datasource.id, full_reindex=True, skip_reindex=False
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, prompt, minimal_response=False
    )
    assert_tool_triggered(Default.SEARCH_KB, triggered_tools)
    similarity_check.check_similarity(response, expected_response)


@pytest.mark.datasource
@pytest.mark.jira
@pytest.mark.api
def test_edit_description_for_jira_data_source(
    client, datasource_utils, jira_datasource
):
    updated_description = get_random_name()

    datasource_utils.update_jira_datasource(
        jira_datasource.id, description=updated_description
    )

    updated_datasource = client.datasources.get(jira_datasource.id)
    assert_that(updated_datasource.description, equal_to(updated_description))


@pytest.mark.datasource
@pytest.mark.jira
@pytest.mark.api
def test_create_jira_datasource_with_existing_name(datasource_utils, jira_datasource):
    datasource = datasource_utils.get_datasource(jira_datasource.id)

    try:
        datasource_utils.create_jira_datasource(
            name=datasource.name, setting_id=datasource.setting_id
        )
        raise AssertionError("There are no error message for duplicate datasource name")
    except HTTPError as e:
        assert_response(
            e.response,
            409,
            f"An index with the name '{datasource.name}' already exists in the project '{os.getenv('PROJECT_NAME')}'.",
        )
