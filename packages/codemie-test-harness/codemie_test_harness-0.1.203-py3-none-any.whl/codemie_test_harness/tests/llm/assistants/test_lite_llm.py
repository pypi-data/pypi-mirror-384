import pytest
from codemie_sdk.models.integration import CredentialTypes
from hamcrest import assert_that, has_item

from codemie_test_harness.tests.enums.model_types import ModelTypes
from codemie_test_harness.tests.test_data.llm_test_data import MODEL_RESPONSES
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.client_factory import get_client
from codemie_test_harness.tests.utils.constants import test_project_name
from codemie_test_harness.tests.utils.env_resolver import (
    get_environment,
    EnvironmentResolver,
)
from codemie_test_harness.tests.utils.pytest_utils import check_mark

pytestmark = pytest.mark.skipif(
    EnvironmentResolver.is_sandbox() or EnvironmentResolver.is_localhost(),
    reason="Skipping this tests on sandbox environments",
)


@pytest.fixture(scope="module")
def lite_llm_integration(integration_utils):
    credential_values = CredentialsManager.lite_llm_credentials()
    integration = integration_utils.create_user_integration(
        CredentialTypes.LITE_LLM,
        credential_values,
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


@pytest.fixture(scope="function")
def invalid_lite_llm_integration(integration_utils):
    credential_values = CredentialsManager.invalid_lite_llm_credentials()
    integration = integration_utils.create_user_integration(
        CredentialTypes.LITE_LLM,
        credential_values,
        project_name=test_project_name,
    )
    yield integration
    if integration:
        integration_utils.delete_integration(integration)


def pytest_generate_tests(metafunc):
    if "model_type" in metafunc.fixturenames:
        is_smoke = check_mark(metafunc, "smoke")
        test_data = []
        env = get_environment()
        if is_smoke:
            available_models = get_client().llms.list()
            for model in available_models:
                test_data.append(pytest.param(model.base_name))
        else:
            for model_data in MODEL_RESPONSES:
                test_data.append(
                    pytest.param(
                        model_data.model_type,
                        marks=pytest.mark.skipif(
                            env not in model_data.environments,
                            reason=f"Skip on non {'/'.join(str(env) for env in model_data.environments[:-1])} envs",
                        ),
                    )
                )

        metafunc.parametrize("model_type", test_data)


@pytest.mark.assistant
@pytest.mark.lite_llm
@pytest.mark.api
def test_assistant_with_different_models_in_lite_llm(
    llm_utils,
    lite_llm_integration,
    assistant_utils,
    model_type,
    similarity_check,
):
    assert_that(
        [row.base_name for row in llm_utils.list_llm_models()],
        has_item(model_type),
        f"{model_type} is missing in backend response",
    )
    assistant = assistant_utils.create_assistant(model_type)
    response = assistant_utils.ask_assistant(assistant, "Just say one word: 'Hello'")

    if model_type in [ModelTypes.DEEPSEEK_R1, ModelTypes.RLAB_QWQ_32B]:
        response = "\n".join(response.split("\n")[-3:])
    similarity_check.check_similarity(response, "Hello")


@pytest.mark.assistant
@pytest.mark.lite_llm
@pytest.mark.api
def test_assistant_with_invalid_lite_llm(
    invalid_lite_llm_integration,
    assistant,
    assistant_utils,
):
    assistant = assistant(project_name=test_project_name)
    response = assistant_utils.ask_assistant(assistant, "Just say one word: 'Hello'")
    assert_that(response.startswith("AI Agent run failed with error: Error code: 401"))
