import json

import pytest
from hamcrest import assert_that, equal_to

from codemie_test_harness.tests.enums.tools import Default
from codemie_test_harness.tests.test_data.assistant_test_data import (
    EXCEL_TOOL_TEST_DATA,
    DOCX_TOOL_TEST_DATA,
)
from codemie_test_harness.tests.test_data.file_test_data import file_test_data
from codemie_test_harness.tests.test_data.output_schema_test_data import output_schema
from codemie_test_harness.tests.utils.base_utils import (
    get_random_name,
    assert_tool_triggered,
)
from codemie_test_harness.tests.utils.constants import FILES_PATH
from codemie_test_harness.tests.utils.yaml_utils import AssistantModel, StateModel


@pytest.mark.workflow
@pytest.mark.api
@pytest.mark.smoke
def test_workflow_with_json_output_schema(default_llm, workflow, workflow_utils):
    assistant_and_state_name = get_random_name()

    assistant = AssistantModel(
        id=assistant_and_state_name,
        model=default_llm.base_name,
        system_prompt="You are a helpful assistant.",
    )

    state = StateModel(
        id=assistant_and_state_name,
        assistant_id=assistant_and_state_name,
        output_schema=json.dumps(output_schema),
    )

    workflow = workflow(
        workflow_name=get_random_name(),
        assistant_model=assistant,
        state_model=state,
    )

    response = workflow_utils.execute_workflow(
        workflow.id, assistant_and_state_name, user_input="1+1?"
    )

    assert_that(json.loads(response)["results"][0], equal_to(2))


@pytest.mark.workflow
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.file
@pytest.mark.parametrize(
    "file_name, expected_response, expected_tool",
    file_test_data,
    ids=[f"{row[0]}" for row in file_test_data],
)
def test_workflow_with_user_input_and_file_attachment(
    workflow_with_virtual_assistant,
    workflow_utils,
    assistant_utils,
    file_name,
    expected_response,
    expected_tool,
    similarity_check,
):
    """
    Test workflow execution with user input that includes file attachment.

    This test demonstrates how workflows can handle file attachments by:
    1. Uploading a file
    2. Creating a workflow with file processing capabilities
    3. Executing the workflow with user input that references the uploaded file
    4. Verifying that file processing tools are triggered
    """
    assistant_and_state_name = get_random_name()

    # Upload file to get file URL
    upload_response = workflow_utils.upload_file(FILES_PATH / file_name)
    file_url = upload_response.files[0].file_url

    # Create workflow with virtual assistant that has file analysis capabilities
    # Note: File analysis tools are automatically available when files are processed
    system_prompt = "You are a helpful assistant that can analyze and process files. "

    workflow_instance = workflow_with_virtual_assistant(
        assistant_and_state_name=assistant_and_state_name,
        system_prompt=system_prompt,
        task=(
            "Analyze the uploaded file from the provided file URL and give a detailed summary. "
            "Use the appropriate file analysis tools based on the file type to extract and process the content."
        ),
    )

    # Prepare user input that includes file reference
    user_input = "Please provide a summary about file content."

    # Execute workflow
    response = workflow_utils.execute_workflow(
        workflow_instance.id,
        assistant_and_state_name,
        user_input=user_input,
        file_name=file_url,
    )

    # Extract triggered tools from execution
    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_instance
    )

    assert_tool_triggered(expected_tool, triggered_tools)
    similarity_check.check_similarity(response, expected_response)


@pytest.mark.workflow
@pytest.mark.file
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.parametrize("prompt, expected_response", EXCEL_TOOL_TEST_DATA)
def test_workflow_excel_tool_extended_functionality(
    workflow_with_virtual_assistant,
    workflow_utils,
    similarity_check,
    prompt,
    expected_response,
):
    """
    Test extended Excel tool functionality with various scenarios in workflow.

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
    assistant_and_state_name = get_random_name()

    # Upload file to get file URL
    upload_response = workflow_utils.upload_file(FILES_PATH / "test_extended.xlsx")
    file_url = upload_response.files[0].file_url

    # Create workflow with virtual assistant that has Excel file processing capabilities
    system_prompt = "You have all required information in initial prompt. Do not ask additional questions and proceed with request."

    workflow_instance = workflow_with_virtual_assistant(
        assistant_and_state_name=assistant_and_state_name,
        system_prompt=system_prompt,
        task=prompt,
    )

    # Execute workflow with the file URL
    response = workflow_utils.execute_workflow(
        workflow_instance.id,
        assistant_and_state_name,
        user_input="Process the uploaded Excel file as requested.",
        file_name=file_url,
    )

    # Extract triggered tools from execution
    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_instance
    )

    assert_tool_triggered(Default.EXCEL_TOOL, triggered_tools)
    similarity_check.check_similarity(response, expected_response)


@pytest.mark.workflow
@pytest.mark.file
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.parametrize("prompt, expected_response", DOCX_TOOL_TEST_DATA)
def test_workflow_docx_tool_extended_functionality(
    workflow_with_virtual_assistant,
    workflow_utils,
    similarity_check,
    prompt,
    expected_response,
):
    """
    Test extended Docx tool functionality with various scenarios in workflow.

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
    assistant_and_state_name = get_random_name()

    # Upload file to get file URL
    upload_response = workflow_utils.upload_file(FILES_PATH / "test_extended.docx")
    file_url = upload_response.files[0].file_url

    # Create workflow with virtual assistant that has DOCX file processing capabilities
    system_prompt = """You are a helpful assistant that can analyze and process DOCX files.
                       You have all required information in initial prompt.
                       Do not ask additional questions and proceed with request."""

    workflow_instance = workflow_with_virtual_assistant(
        assistant_and_state_name=assistant_and_state_name,
        system_prompt=system_prompt,
        task=prompt,
    )

    # Execute workflow with the file URL
    response = workflow_utils.execute_workflow(
        workflow_instance.id,
        assistant_and_state_name,
        user_input="Process the uploaded DOCX file as requested.",
        file_name=file_url,
    )

    # Extract triggered tools from execution
    triggered_tools = workflow_utils.extract_triggered_tools_from_execution(
        workflow_instance
    )

    assert_tool_triggered(Default.DOCX_TOOL, triggered_tools)
    similarity_check.check_similarity(response, expected_response)
