import pytest
from codemie_sdk.models.conversation import Conversation, ConversationDetails
from hamcrest import (
    assert_that,
    has_length,
    instance_of,
    all_of,
    has_property,
    greater_than_or_equal_to,
    has_item,
    equal_to,
    has_entry,
)

from codemie_test_harness.tests.utils.base_utils import get_random_name


@pytest.mark.assistant
@pytest.mark.conversations
@pytest.mark.api
def test_list_conversations(assistant, assistant_utils, conversation_utils):
    assistant = assistant()
    assistant_utils.ask_assistant(assistant, f"prompt {get_random_name()}")

    conversations = conversation_utils.list_conversations()

    assert_that(conversations, instance_of(list))
    assert_that(conversations, has_length(greater_than_or_equal_to(1)))

    conversation = conversations[0]
    assert_that(
        conversation,
        all_of(
            instance_of(Conversation),
            has_property("id"),
            has_property("name"),
            has_property("folder"),
            has_property("pinned"),
            has_property("date"),
            has_property("assistant_ids", instance_of(list)),
            has_property("initial_assistant_id"),
        ),
    )


@pytest.mark.assistant
@pytest.mark.conversations
@pytest.mark.api
def test_get_specific_conversation(assistant, assistant_utils, conversation_utils):
    prompt = f"prompt {get_random_name()}"
    assistant = assistant()

    assistant_utils.ask_assistant(assistant, prompt)

    conversations = conversation_utils.list_conversations()

    first_conversation = conversations[0]
    conversation = conversation_utils.get_conversation_by_id(first_conversation.id)
    assert_that(
        conversation,
        all_of(
            instance_of(ConversationDetails),
            has_property("id", first_conversation.id),
            has_property("conversation_name", prompt),
            has_property("initial_assistant_id", assistant.id),
        ),
    )


@pytest.mark.assistant
@pytest.mark.conversations
@pytest.mark.api
def test_get_conversation_by_assistant_id(
    assistant, assistant_utils, conversation_utils
):
    prompt = f"prompt {get_random_name()}"
    assistant = assistant()

    assistant_utils.ask_assistant(assistant, prompt)
    conversation = conversation_utils.get_conversation_by_assistant_id(assistant.id)
    assert_that(
        conversation[0],
        all_of(
            instance_of(Conversation),
            has_property("id", conversation[0].id),
            has_property("name", prompt),
            has_property("assistant_ids", has_item(assistant.id)),
            has_property("initial_assistant_id", assistant.id),
        ),
    )


@pytest.mark.assistant
@pytest.mark.conversations
@pytest.mark.api
def test_delete_conversation(assistant, assistant_utils, conversation_utils):
    prompt = f"prompt {get_random_name()}"
    assistant = assistant()

    assistant_utils.ask_assistant(assistant, prompt)
    conversation = conversation_utils.get_conversation_by_assistant_id(assistant.id)

    delete_response = conversation_utils.delete_conversation(conversation[0].id)
    assert_that(
        delete_response["message"],
        equal_to("Specified conversation removed"),
        "Conversation delete response is not as expected.",
    )


@pytest.mark.assistant
@pytest.mark.conversations
@pytest.mark.api
def test_get_non_existent_conversation(assistant, assistant_utils, conversation_utils):
    invalid_id = get_random_name()
    with pytest.raises(Exception) as exc_info:
        conversation_utils.get_conversation_by_id(invalid_id)

    error_response = exc_info.value.response.json()
    assert_that(
        error_response["error"],
        all_of(
            has_entry("message", "Conversation not found"),
            has_entry(
                "details",
                f"The conversation with ID [{invalid_id}] could not be found in the system.",
            ),
            has_entry(
                "help",
                "Please verify the conversation ID and try again. If you believe this is an error, contact support.",
            ),
        ),
    )
