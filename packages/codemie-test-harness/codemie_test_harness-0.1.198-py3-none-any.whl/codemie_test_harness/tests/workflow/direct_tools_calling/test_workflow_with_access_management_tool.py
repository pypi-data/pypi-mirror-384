import copy
import json
import random

import pytest

from codemie_test_harness.tests.enums.tools import AccessManagementTool
from codemie_test_harness.tests.test_data.direct_tools.keycloak_tool_test_data import (
    KEYCLOAK_DIRECT_TOOL_PROMPT,
    KEYCLOAK_DIRECT_TOOL_RESPONSE,
)
from codemie_test_harness.tests.utils.base_utils import get_random_name


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.keycloak
@pytest.mark.api
def test_workflow_with_keycloak_tool_direct(
    keycloak_integration, workflow_utils, workflow_with_tool, similarity_check
):
    assistant_and_state_name = get_random_name()

    test_workflow = workflow_with_tool(
        assistant_and_state_name,
        AccessManagementTool.KEYCLOAK,
        integration=keycloak_integration,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id,
        assistant_and_state_name,
        user_input=json.dumps(KEYCLOAK_DIRECT_TOOL_PROMPT),
    )
    similarity_check.check_similarity(response, KEYCLOAK_DIRECT_TOOL_RESPONSE)


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.keycloak
@pytest.mark.api
def test_workflow_with_keycloak_tool_with_hardcoded_args(
    keycloak_integration, workflow_utils, workflow_with_tool, similarity_check
):
    assistant_and_state_name = get_random_name()

    test_workflow = workflow_with_tool(
        assistant_and_state_name,
        AccessManagementTool.KEYCLOAK,
        integration=keycloak_integration,
        tool_args=KEYCLOAK_DIRECT_TOOL_PROMPT,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id, assistant_and_state_name
    )
    similarity_check.check_similarity(response, KEYCLOAK_DIRECT_TOOL_RESPONSE)


@pytest.mark.workflow
@pytest.mark.direct_tool
@pytest.mark.keycloak
@pytest.mark.api
def test_workflow_with_keycloak_tool_with_overriding_args(
    keycloak_integration, workflow_utils, workflow_with_tool, similarity_check
):
    assistant_and_state_name = get_random_name()

    args_copy = copy.deepcopy(KEYCLOAK_DIRECT_TOOL_PROMPT)
    args_copy = {key: random.randint(1, 10) for key in args_copy}

    test_workflow = workflow_with_tool(
        assistant_and_state_name,
        AccessManagementTool.KEYCLOAK,
        integration=keycloak_integration,
        tool_args=args_copy,
    )
    response = workflow_utils.execute_workflow(
        test_workflow.id,
        assistant_and_state_name,
        user_input=json.dumps(KEYCLOAK_DIRECT_TOOL_PROMPT),
    )
    similarity_check.check_similarity(response, KEYCLOAK_DIRECT_TOOL_RESPONSE)
