import copy
import json
import random

import pytest

from codemie_test_harness.tests.test_data.direct_tools.report_portal_tools_test_data import (
    report_portal_tools_test_data,
)
from codemie_test_harness.tests.utils.base_utils import get_random_name


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.report_portal
@pytest.mark.api
@pytest.mark.parametrize(
    "toolkit,tool_name,prompt,expected_response",
    report_portal_tools_test_data,
    ids=[f"{row[0]}_{row[1]}" for row in report_portal_tools_test_data],
)
def test_workflow_with_report_portal_tool_direct(
    report_portal_integration,
    workflow_utils,
    workflow_with_tool,
    similarity_check,
    toolkit,
    tool_name,
    prompt,
    expected_response,
):
    assistant_and_state_name = get_random_name()

    test_workflow = workflow_with_tool(
        assistant_and_state_name,
        tool_name,
        integration=report_portal_integration,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id,
        assistant_and_state_name,
        user_input=json.dumps(prompt),
    )
    similarity_check.check_similarity(response, expected_response)


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.report_portal
@pytest.mark.api
@pytest.mark.parametrize(
    "toolkit,tool_name,prompt,expected_response",
    report_portal_tools_test_data,
    ids=[f"{row[0]}_{row[1]}" for row in report_portal_tools_test_data],
)
def test_workflow_with_report_portal_tool_with_hardcoded_args(
    report_portal_integration,
    workflow_utils,
    workflow_with_tool,
    similarity_check,
    toolkit,
    tool_name,
    prompt,
    expected_response,
):
    assistant_and_state_name = get_random_name()

    test_workflow = workflow_with_tool(
        assistant_and_state_name,
        tool_name,
        integration=report_portal_integration,
        tool_args=prompt,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id, assistant_and_state_name
    )
    similarity_check.check_similarity(response, expected_response)


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.report_portal
@pytest.mark.api
@pytest.mark.parametrize(
    "toolkit,tool_name,prompt,expected_response",
    report_portal_tools_test_data,
    ids=[f"{row[0]}_{row[1]}" for row in report_portal_tools_test_data],
)
def test_workflow_with_report_portal_tool_with_overriding_args(
    report_portal_integration,
    workflow_utils,
    workflow_with_tool,
    similarity_check,
    toolkit,
    tool_name,
    prompt,
    expected_response,
):
    assistant_and_state_name = get_random_name()

    args_copy = copy.deepcopy(prompt)
    args_copy = {key: random.randint(1, 10) for key in args_copy}

    test_workflow = workflow_with_tool(
        assistant_and_state_name,
        tool_name,
        integration=report_portal_integration,
        tool_args=args_copy,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id,
        assistant_and_state_name,
        user_input=json.dumps(prompt),
    )
    similarity_check.check_similarity(response, expected_response)
