import pytest

from codemie_test_harness.tests import CredentialsManager, PROJECT, TEST_USER
from codemie_test_harness.tests.test_data.google_datasource_test_data import (
    GOOGLE_DOC_URL,
)
from codemie_test_harness.tests.ui.pageobject.datasources.create_edit_datasource_page import (
    CreateEditDatasourcePage,
)
from codemie_test_harness.tests.ui.pageobject.datasources.datasource_page import (
    DataSourcePage,
)
from codemie_test_harness.tests.ui.test_data.datasource_test_data import (
    DataSourceType,
    DataSourceFilterType,
    DataSourceStatus,
    SUBTITLE_CREATE_DATASOURCE,
    TITLE_CREATE_DATASOURCE,
)
from codemie_test_harness.tests.utils.constants import FILES_PATH


@pytest.mark.datasource
@pytest.mark.ui
def test_open_create_datasource_page_and_elements(page):
    """Open Create Datasource page and verify critical elements."""
    create_page = CreateEditDatasourcePage(page)

    create_page.navigate_to()
    create_page.sidebar.should_see_title_subtitle(
        TITLE_CREATE_DATASOURCE, SUBTITLE_CREATE_DATASOURCE
    )
    create_page.should_see_main_fields()

    create_page.select_datasource_type(DataSourceType.GIT)
    create_page.should_see_git_fields()

    create_page.select_datasource_type(DataSourceFilterType.CONFLUENCE)
    create_page.should_see_confluence_cql_field()
    create_page.should_see_integration_input_or_button()

    create_page.select_datasource_type(DataSourceFilterType.JIRA)
    create_page.should_see_jira_jql_field()
    create_page.should_see_integration_input_or_button()

    create_page.select_datasource_type(DataSourceFilterType.FILE)
    create_page.should_see_file_fields()
    create_page.select_datasource_type(DataSourceFilterType.GOOGLE)
    create_page.should_see_google_fields()


@pytest.mark.datasource
@pytest.mark.ui
def test_datasource_creation_validation(page):
    """Test create datasource without data and observing errors."""
    create_page = CreateEditDatasourcePage(page)

    create_page.navigate_to()
    create_page.select_datasource_type(DataSourceType.GIT).click_create()
    create_page.should_see_error_for_empty_main_fields()
    create_page.should_see_error_for_empty_git_fields()

    create_page.select_datasource_type(DataSourceFilterType.CONFLUENCE).click_create()
    create_page.should_see_error_for_empty_main_fields()
    create_page.should_see_error_for_empty_confluence_fields()

    create_page.select_datasource_type(DataSourceFilterType.JIRA).click_create()
    create_page.should_see_error_for_empty_main_fields()
    create_page.should_see_error_for_empty_jira_fields()

    create_page.select_datasource_type(DataSourceFilterType.FILE).click_create()
    create_page.should_see_error_for_empty_main_fields()
    create_page.should_see_error_for_empty_file_fields()

    create_page.select_datasource_type(DataSourceFilterType.GOOGLE).click_create()
    create_page.should_see_error_for_empty_main_fields()
    create_page.should_see_error_for_empty_google_fields()


@pytest.mark.datasource
@pytest.mark.ui
def test_create_git_datasource(page, git_integration):
    """Test creating a new datasource with all required fields."""
    datasource_page = DataSourcePage(page)
    create_page = CreateEditDatasourcePage(page)

    create_page.navigate_to()
    datasource = create_page.create_git_datasource(
        project_name=PROJECT,
        repo_link=CredentialsManager.get_parameter("GITLAB_PROJECT"),
        branch="main",
        integration=git_integration.alias,
    )

    datasource_page.should_see_table_row_with_values(
        name=datasource,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.CODE,
        created_by=TEST_USER,
    )


@pytest.mark.datasource
@pytest.mark.ui
def test_create_confluence_datasource(page, confluence_integration):
    """Test creating a new datasource with all required fields."""
    datasource_page = DataSourcePage(page)
    create_page = CreateEditDatasourcePage(page)

    create_page.navigate_to()
    datasource = create_page.create_confluence_datasource(
        project_name=PROJECT,
        cql_query=CredentialsManager.confluence_cql(),
        integration=confluence_integration.alias,
    )

    datasource_page.should_see_table_row_with_values(
        name=datasource,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.CONFLUENCE,
        created_by=TEST_USER,
    )


@pytest.mark.datasource
@pytest.mark.ui
def test_create_jira_datasource(page, jira_integration):
    """Test creating a new datasource with all required fields."""
    datasource_page = DataSourcePage(page)
    create_page = CreateEditDatasourcePage(page)

    create_page.navigate_to()
    datasource = create_page.create_jira_datasource(
        project_name=PROJECT,
        jql_query=CredentialsManager.jira_jql(),
        integration=jira_integration.alias,
    )

    datasource_page.should_see_table_row_with_values(
        name=datasource,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.JIRA,
        created_by=TEST_USER,
    )


@pytest.mark.datasource
@pytest.mark.ui
def test_create_file_datasource(page):
    """Test creating a new datasource with all required fields."""
    datasource_page = DataSourcePage(page)
    create_page = CreateEditDatasourcePage(page)

    create_page.navigate_to()
    datasource = create_page.create_file_datasource(
        project_name=PROJECT,
        file_path=[str(FILES_PATH / "test.txt")],
    )

    datasource_page.should_see_table_row_with_values(
        name=datasource,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.FILE,
        created_by=TEST_USER,
    )


@pytest.mark.datasource
@pytest.mark.ui
def test_create_google_datasource(page):
    """Test creating a new datasource with all required fields."""
    datasource_page = DataSourcePage(page)
    create_page = CreateEditDatasourcePage(page)

    create_page.navigate_to()
    datasource = create_page.create_google_datasource(
        project_name=PROJECT,
        google_doc_link=GOOGLE_DOC_URL,
    )

    datasource_page.should_see_table_row_with_values(
        name=datasource,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.GOOGLE,
        created_by=TEST_USER,
    )
