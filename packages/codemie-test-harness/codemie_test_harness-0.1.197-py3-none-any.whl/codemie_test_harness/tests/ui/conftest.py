import logging
import os
from datetime import datetime
from time import sleep

import pytest
from codemie_sdk.models.conversation import ConversationCreateRequest
from codemie_sdk.models.integration import IntegrationType
from reportportal_client import RPLogger, RPLogHandler
from requests import HTTPError

from codemie_test_harness.tests import autotest_entity_prefix
from codemie_test_harness.tests.ui import conversation_ids
from codemie_test_harness.tests.ui.pageobject.login_page import LoginPage
from codemie_test_harness.tests.utils.client_factory import get_client
from codemie_test_harness.tests.utils.env_resolver import EnvironmentResolver

# Create ReportPortal logger
logging.setLoggerClass(RPLogger)
rp_logger = logging.getLogger("reportportal_logger")
rp_logger.setLevel(logging.DEBUG)
rp_logger.addHandler(RPLogHandler())


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    """Capture screenshot on test failure"""
    yield
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name = request.node.name

        # Create screenshots directory
        screenshot_dir = "test_screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)

        # Capture screenshot
        screenshot_file_path = os.path.join(
            screenshot_dir, f"failure_{test_name}_{timestamp}.png"
        )

        page.screenshot(path=screenshot_file_path, full_page=True)
        with open(screenshot_file_path, "rb") as image_file:
            file_data = image_file.read()
            rp_logger.info(
                f"Test failed - Screenshot captured: {test_name}",
                attachment={
                    "name": f"{test_name}_failure_screenshot.png",
                    "data": file_data,
                    "mime": "image/png",
                },
            )


@pytest.fixture(autouse=True)
def login(page):
    page = LoginPage(page)
    page.navigate_to()
    if not EnvironmentResolver.is_localhost():
        page.login(os.getenv("AUTH_USERNAME"), os.getenv("AUTH_PASSWORD"))
    page.should_see_new_release_popup()
    page.pop_up.close_popup()
    page.should_not_see_new_release_popup()


@pytest.fixture(scope="session", autouse=True)
def browser_context_args(browser_context_args):
    width = int(os.getenv("VIEWPORT_WIDTH", 1920))
    height = int(os.getenv("VIEWPORT_HEIGHT", 1080))
    return {
        **browser_context_args,
        "viewport": {
            "width": width,
            "height": height,
        },
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("FRONTEND_URL")


@pytest.fixture(scope="function")
def create_new_conversation():
    conversation = get_client().conversations.create(
        ConversationCreateRequest(folder="")
    )
    yield conversation
    try:
        get_client().conversations.delete(conversation.get("id"))
    except HTTPError:
        pass


@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {
        "headless": os.getenv("HEADLESS", "false").lower() == "true",
        "slow_mo": 150,
    }


def pytest_sessionfinish(session):
    """Run cleanup code after all tests have finished."""
    clean_up_timeout = 1 if EnvironmentResolver.is_production() else 0
    client = get_client()
    prefix = autotest_entity_prefix
    # Assistants
    assistants = client.assistants.list(filters={"search": prefix}, per_page=200)
    for assistant in assistants:
        if prefix in assistant.name:
            client.assistants.delete(assistant_id=assistant.id)
            sleep(clean_up_timeout)
            conversations = client.conversations.list_by_assistant_id(assistant.id)
            for conversation in conversations:
                client.conversations.delete(conversation.id)
                sleep(clean_up_timeout)
    # Integrations
    integrations = client.integrations.list(
        setting_type=IntegrationType.PROJECT,
        filters={"search": autotest_entity_prefix},
        per_page=200,
    )
    for integration in integrations:
        if prefix in integration.alias:
            client.integrations.delete(
                setting_id=integration.id, setting_type=IntegrationType.PROJECT
            )
            sleep(clean_up_timeout)
    integrations = client.integrations.list(
        setting_type=IntegrationType.USER,
        filters={"search": autotest_entity_prefix},
        per_page=200,
    )
    for integration in integrations:
        if prefix in integration.alias:
            client.integrations.delete(
                setting_id=integration.id, setting_type=IntegrationType.USER
            )
            sleep(clean_up_timeout)
    for conversation_id in conversation_ids:
        client.conversations.delete(conversation_id)
        sleep(clean_up_timeout)
