import json
import os
import uuid

import pytest
from hamcrest import assert_that, equal_to, greater_than, is_not, empty
from pydantic import BaseModel
from requests import HTTPError

from codemie_sdk.models.assistant import (
    AssistantUpdateRequest,
    AssistantChatRequest,
    ChatMessage,
    ChatRole,
)
from codemie_test_harness.tests import TEST_USER, PROJECT, LANGFUSE_TRACES_ENABLED
from codemie_test_harness.tests.test_data.assistant_test_data import (
    EXCEL_TOOL_TEST_DATA,
    DOCX_TOOL_TEST_DATA,
)
from codemie_test_harness.tests.test_data.file_test_data import (
    files_with_different_types_test_data,
    file_test_data,
    RESPONSE_FOR_TWO_FILES_UPLOADED,
)
from codemie_test_harness.tests.test_data.output_schema_test_data import output_schema
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_tool_triggered,
)
from codemie_test_harness.tests.enums.tools import Default
from codemie_test_harness.tests.utils.constants import FILES_PATH
from codemie_test_harness.tests.utils.file_utils import save_file

system_prompt_for_chatting_with_files = """Your task is to show the content of the file. You MUST NOT:
    - analyze the content
    - use any scripts
    - do not wrap content in formatting blocks
"""


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_create_assistant(assistant_utils, default_llm):
    response = assistant_utils.send_create_assistant_request()
    message = response[0].get("message")
    assert_that(
        message, equal_to("Specified assistant saved"), "Unexpected response message."
    )


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_get_all_assistants(search_utils):
    response = search_utils.list_assistants(filters=None)
    ids = list(map(lambda item: item["id"], response))

    assert_that(len(ids), greater_than(0), "No assistants found.")


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_get_prebuilt_assistants(assistant_utils):
    response = assistant_utils.get_prebuilt_assistant()
    ids = list(map(lambda item: item["id"], response))

    assert_that(len(ids), greater_than(0), "No prebuilt assistants found.")


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_get_users_assistants(assistant_utils, search_utils):
    assistant_utils.send_create_assistant_request()
    response = search_utils.list_assistants(filters={"created_by": TEST_USER})
    users = list(map(lambda item: item["created_by"]["name"], response))

    assert_that(TEST_USER in users, f"No assistants created by '{TEST_USER}' found.")


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_get_assistant_context(assistant_utils):
    response = assistant_utils.get_assistant_context(PROJECT)

    assert_that(len(response), greater_than(0), "No assistants context found.")


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_get_available_tools(assistant_utils):
    response = assistant_utils.get_assistant_tools()

    assert_that(len(response), greater_than(0), "No assistants tools found.")


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_get_assistant_by_id(assistant_utils):
    assistant_name = get_random_name()
    assistant_utils.create_assistant(assistant_name=assistant_name)
    response = assistant_utils.get_assistant_by_name(assistant_name)

    test_assistant = assistant_utils.get_assistant_by_id(response.id)
    assert_that(
        test_assistant["name"],
        equal_to(assistant_name),
        f"No assistants found with the given name: {assistant_name}",
    )


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_get_assistant_by_slug(assistant_utils):
    assistant_name = get_random_name()
    assistant_utils.create_assistant(assistant_name=assistant_name)
    response = assistant_utils.get_assistant_by_name(assistant_name)

    test_assistant = assistant_utils.get_assistant_by_slug(response.slug)
    assert_that(
        test_assistant["name"],
        equal_to(assistant_name),
        f"No assistants found with the given slug: {response.slug}",
    )


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_update_assistant(assistant_utils, default_llm):
    assistant_name = get_random_name()
    assistant_utils.create_assistant(assistant_name=assistant_name)
    response = assistant_utils.get_assistant_by_name(assistant_name)
    updated_description = "Integration test assistant [updated]"
    updated_system_prompt = "Integration test assistant [updated]"
    request = AssistantUpdateRequest(
        name=assistant_name,
        slug=assistant_name,
        description=updated_description,
        shared=False,
        system_prompt=updated_system_prompt,
        project=PROJECT,
        llm_model_type=default_llm.base_name,
    )

    update_response = assistant_utils.update_assistant(response.id, request)

    message = update_response.get("message")
    assert_that(
        message, equal_to("Specified assistant updated"), "Unexpected response message."
    )
    updated_assistant = assistant_utils.get_assistant_by_id(response.id)
    assert_that(
        updated_assistant["system_prompt"],
        equal_to(updated_system_prompt),
        "System prompt was not updated correctly.",
    )
    assert_that(
        updated_assistant["description"],
        equal_to(updated_description),
        "Description was not updated correctly.",
    )


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_delete_assistant(assistant_utils, search_utils):
    assistant_name = get_random_name()
    assistant_utils.create_assistant(assistant_name=assistant_name)
    response = assistant_utils.get_assistant_by_name(assistant_name)
    delete_response = assistant_utils.delete_assistant(response)
    message = delete_response.get("message")

    assert_that(
        message, equal_to("Specified assistant removed"), "Unexpected response message."
    )
    search_response = search_utils.list_assistants(filters={"search": assistant_name})

    assert_that(len(search_response), equal_to(0), "Assistant was not deleted")


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_ask_assistant(assistant_utils):
    test_assistant = assistant_utils.create_assistant()
    chat_request = AssistantChatRequest(
        system_prompt="Just answer IT related questions",
        text="What can you do?",
        conversation_id=str(uuid.uuid4()),
        stream=False,
        top_k=10,
        background_task=True,
        metadata={"langfuse_traces_enabled": LANGFUSE_TRACES_ENABLED},
    )
    response = assistant_utils.send_chat_request(test_assistant, chat_request)

    assert_that(response.task_id, is_not(empty()), "No response from assistant")


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.skip(reason="Not implemented yet")
def test_export_assistant(assistant_utils):
    assistant_name = get_random_name()
    assistant_utils.create_assistant(assistant_name=assistant_name)
    get_response = assistant_utils.get_assistant_by_name(assistant_name)
    export_response = assistant_utils.export_assistant(get_response.id)
    target_file_path = "./exported_assistant.tar"
    save_file(export_response.content, target_file_path)

    assert_that(
        os.path.getsize(target_file_path), greater_than(0), "Failed to export assistant"
    )


@pytest.mark.assistant
@pytest.mark.file
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.testcase("EPMCDME-4001, EPMCDME-4002, EPMCDME-2527")
@pytest.mark.parametrize(
    "file_name,expected_response,expected_tool",
    file_test_data,
    ids=[f"{row[0]}" for row in file_test_data],
)
def test_create_assistant_and_prompt_with_file(
    assistant_utils,
    assistant,
    similarity_check,
    file_name,
    expected_response,
    expected_tool,
):
    prompt = (
        f"What is the content/text of the {file_name}. Show information from ALL pages. "
        "For PDF use 'Text' for query. If provided file is CSV then run python_repl_ast tool and show first 5 rows."
        "For images explain what you see on it."
        "For excel show data from the sheet with name 'Sheet1'"
    )

    assistant = assistant(system_prompt=system_prompt_for_chatting_with_files)

    uploaded_file = assistant_utils.upload_file_to_chat(FILES_PATH / file_name)
    file_url = uploaded_file.get("file_url")

    conversation_id = str(uuid.uuid4())

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant,
        prompt,
        file_urls=[file_url],
        conversation_id=conversation_id,
        minimal_response=False,
    )
    assert_tool_triggered(expected_tool, triggered_tools)
    similarity_check.check_similarity(response, expected_response)

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, prompt, conversation_id=conversation_id, minimal_response=False
    )
    assert_tool_triggered(expected_tool, triggered_tools)
    similarity_check.check_similarity(response, expected_response)


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_assistant_has_an_access_to_the_history(
    assistant_utils,
    assistant,
    similarity_check,
):
    assistant = assistant()

    conversation_id = str(uuid.uuid4())

    response = assistant_utils.ask_assistant(
        assistant,
        "1+1? No need to generate any code, just return result.",
        conversation_id=conversation_id,
    )
    similarity_check.check_similarity(response, "1 + 1 equals 2.")

    response = assistant_utils.ask_assistant(
        assistant,
        "Add +5 to the previous result. No need to generate any code, just return result.",
        conversation_id=conversation_id,
    )
    similarity_check.check_similarity(response, "2 + 5 equals 7.", 90)


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_passing_history_to_chat(
    assistant_utils,
    assistant,
    similarity_check,
):
    assistant = assistant()

    conversation_id = str(uuid.uuid4())

    response = assistant_utils.ask_assistant(
        assistant, "1+1?", conversation_id=conversation_id
    )
    similarity_check.check_similarity(response, "1 + 1 equals 2.")

    response = assistant_utils.ask_assistant(
        assistant,
        "Add +5 to the previous result. No need to generate any code, just return result. Example: a + b equals c.",
        conversation_id=conversation_id,
        history=[ChatMessage(role=ChatRole.ASSISTANT, message="1 + 2 equals 3.")],
    )
    similarity_check.check_similarity(response, "3 + 5 equals 8.", 90)


@pytest.mark.assistant
@pytest.mark.file
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.parametrize(
    "file_name",
    files_with_different_types_test_data,
)
def test_upload_file_to_chat(
    assistant_utils,
    file_name,
):
    try:
        assistant_utils.upload_file_to_chat(FILES_PATH / file_name)
    except HTTPError as e:
        error_details = json.loads(e.response.content)["error"]["details"]
        raise AssertionError(f"Error on uploading file to chat: {error_details}")


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_chat_with_pydantic_output_schema(assistant_utils, assistant):
    class OutputSchema(BaseModel):
        results: list[int]

    response = assistant_utils.ask_assistant(
        assistant(), "1+1?", output_schema=OutputSchema
    )

    assert_that(response.results[0], equal_to(2))


@pytest.mark.assistant
@pytest.mark.api
@pytest.mark.smoke
def test_chat_with_json_output_schema(assistant_utils, assistant):
    response = assistant_utils.ask_assistant(
        assistant(), "1+1?", output_schema=output_schema
    )

    assert_that(response["results"][0], equal_to(2))


@pytest.mark.assistant
@pytest.mark.file
@pytest.mark.api
@pytest.mark.smoke
def test_create_assistant_and_prompt_with_multiple_files(
    assistant_utils,
    assistant,
    similarity_check,
):
    docx_file = "test.docx"

    ini_file = "test.ini"

    prompt = f"What is the content/text of the {docx_file} and {ini_file} files. Show exact text from ALL pages in format: <file_name><file_content>"

    assistant = assistant(system_prompt=system_prompt_for_chatting_with_files)

    uploaded_docx_file = assistant_utils.upload_file_to_chat(FILES_PATH / docx_file)
    docx_file_url = uploaded_docx_file.get("file_url")

    uploaded_ini_file = assistant_utils.upload_file_to_chat(FILES_PATH / ini_file)
    ini_file_url = uploaded_ini_file.get("file_url")

    conversation_id = str(uuid.uuid4())

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant,
        prompt,
        file_urls=[docx_file_url, ini_file_url],
        conversation_id=conversation_id,
        minimal_response=False,
    )

    assert_tool_triggered((Default.DOCX_TOOL, Default.FILE_ANALYSIS), triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_TWO_FILES_UPLOADED)

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant, prompt, conversation_id=conversation_id, minimal_response=False
    )

    assert_tool_triggered((Default.DOCX_TOOL, Default.FILE_ANALYSIS), triggered_tools)
    similarity_check.check_similarity(response, RESPONSE_FOR_TWO_FILES_UPLOADED)


@pytest.mark.assistant
@pytest.mark.file
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.parametrize("prompt,expected_response", EXCEL_TOOL_TEST_DATA)
def test_excel_tool_extended_functionality(
    assistant_utils, assistant, similarity_check, prompt, expected_response
):
    """
    Test extended Excel tool functionality with various scenarios.

    This test covers:
    - Data extraction from visible sheets only
    - All data including hidden sheets
    - Sheet name listing functionality
    - File statistics and structure analysis
    - Single sheet extraction by index and name
    - Data cleaning and normalization
    - Hidden sheet visibility control
    - Column structure and data type analysis
    - Tabular structure normalization
    - Multi-sheet comprehensive analysis

    """
    assistant_instance = assistant(
        system_prompt="You have all required information in initial prompt. Do not ask additional questions and proceed with request."
    )

    uploaded_file = assistant_utils.upload_file_to_chat(
        FILES_PATH / "test_extended.xlsx"
    )
    file_url = uploaded_file.get("file_url")

    # Send the prompt with the uploaded file
    response, triggered_tools = assistant_utils.ask_assistant(
        assistant_instance, prompt, file_urls=[file_url], minimal_response=False
    )

    assert_tool_triggered(Default.EXCEL_TOOL, triggered_tools)
    similarity_check.check_similarity(response, expected_response)


@pytest.mark.assistant
@pytest.mark.file
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.parametrize("prompt,expected_response", DOCX_TOOL_TEST_DATA)
def test_docx_tool_extended_functionality(
    assistant_utils, assistant, similarity_check, prompt, expected_response
):
    """
    Test extended Docx tool functionality with various scenarios.

    This test covers:
    - Extract plain text using 'text' query
    - Extract text with metadata using 'text_with_metadata' query
    - Extract document structure using 'structure_only' query
    - Extract tables using 'table_extraction' query
    - Generate summary using 'summary' query
    - Perform analysis with custom instructions using 'analyze' query
    - Process specific pages '1-3' using pages parameter
    - Process specific pages '1,5,10' using pages parameter
    - Extract images using 'image_extraction' query
    - Extract text with OCR from images using 'text_with_images' query

    """
    assistant_instance = assistant()

    uploaded_file = assistant_utils.upload_file_to_chat(
        FILES_PATH / "test_extended.docx"
    )
    file_url = uploaded_file.get("file_url")

    # Send the prompt with the uploaded file
    response, triggered_tools = assistant_utils.ask_assistant(
        assistant_instance, prompt, file_urls=[file_url], minimal_response=False
    )

    assert_tool_triggered(Default.DOCX_TOOL, triggered_tools)
    similarity_check.check_similarity(response, expected_response)


@pytest.mark.assistant
# @pytest.mark.api
@pytest.mark.smoke
@pytest.mark.excel_generation
def test_excel_file_generation(assistant_utils, assistant, similarity_check):
    assistant_instance = assistant()

    response = assistant_utils.ask_assistant(
        assistant_instance, "Generate excel with 5 sheets with random data"
    )

    similarity_check.check_similarity(response, "expected_response_here")
