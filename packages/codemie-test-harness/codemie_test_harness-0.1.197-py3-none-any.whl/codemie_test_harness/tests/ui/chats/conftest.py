import pytest

from codemie_test_harness.tests.ui.pageobject.chats.chat_page import ChatPage


@pytest.fixture(scope="function")
def navigate_to_new_chat_page(create_new_conversation):
    def _navigate_to(page):
        chat_id = create_new_conversation.get("id")
        chat_page = ChatPage(page)
        chat_page.navigate_to(chat_id)
        return chat_page

    return _navigate_to
