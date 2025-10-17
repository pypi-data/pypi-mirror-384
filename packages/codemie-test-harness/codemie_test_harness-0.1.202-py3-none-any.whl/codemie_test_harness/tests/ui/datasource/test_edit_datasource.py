import pytest

from codemie_test_harness.tests import PROJECT, TEST_USER
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
    DataSourceStatus,
    DataSourceFilterType,
    UPDATE_SUBTITLE_DATASOURCE,
    UPDATE_TITLE_DATASOURCE,
)
from codemie_test_harness.tests.utils.constants import FILES_PATH


@pytest.mark.datasource
@pytest.mark.ui
def test_edit_git_datasource(
    page, datasource_utils, git_integration, default_embedding_llm
):
    """Test that all main Edit Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    edit_page = CreateEditDatasourcePage(page)

    datasource = datasource_utils.create_gitlab_datasource(
        setting_id=git_integration.id,
        embeddings_model=default_embedding_llm.base_name,
    )

    datasource_page.navigate_to()
    datasource_page.should_see_table_row_with_values(
        name=datasource.name,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.CODE,
        created_by=TEST_USER,
    )

    datasource_page.open_row_action_menu(datasource.name)
    datasource_page.should_see_edit_dropdown_values()
    datasource_page.should_see_edit_dropdown_full_reindex_value()
    datasource_page.click_row_action("Edit")

    edit_page.sidebar.should_see_title_subtitle(
        UPDATE_TITLE_DATASOURCE, UPDATE_SUBTITLE_DATASOURCE
    )
    edit_page.selector.should_see_disabled_multiselect(PROJECT)
    edit_page.should_see_disabled_name_input(datasource.name)
    edit_page.should_see_save_reindex_button()


@pytest.mark.datasource
@pytest.mark.ui
def test_edit_confluence_datasource(page, datasource_utils, confluence_integration):
    """Test that all main Edit Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    edit_page = CreateEditDatasourcePage(page)

    datasource = datasource_utils.create_confluence_datasource(
        setting_id=confluence_integration.id,
    )

    datasource_page.navigate_to()
    datasource_page.should_see_table_row_with_values(
        name=datasource.name,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.CONFLUENCE,
        created_by=TEST_USER,
    )

    datasource_page.open_row_action_menu(datasource.name)
    datasource_page.should_see_edit_dropdown_values()
    datasource_page.should_see_edit_dropdown_full_reindex_value()
    datasource_page.click_row_action("Edit")

    edit_page.sidebar.should_see_title_subtitle(
        UPDATE_TITLE_DATASOURCE, UPDATE_SUBTITLE_DATASOURCE
    )
    edit_page.selector.should_see_disabled_multiselect(PROJECT)
    edit_page.should_see_disabled_name_input(datasource.name)
    edit_page.should_see_save_reindex_button()


@pytest.mark.datasource
@pytest.mark.ui
def test_edit_jira_datasource(page, datasource_utils, jira_integration):
    """Test that all main Edit Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    edit_page = CreateEditDatasourcePage(page)

    datasource = datasource_utils.create_jira_datasource(
        setting_id=jira_integration.id,
    )

    datasource_page.navigate_to()
    datasource_page.should_see_table_row_with_values(
        name=datasource.name,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.JIRA,
        created_by=TEST_USER,
    )

    datasource_page.open_row_action_menu(datasource.name)
    datasource_page.should_see_edit_dropdown_values()
    datasource_page.should_see_edit_dropdown_index_values()
    datasource_page.click_row_action("Edit")

    edit_page.sidebar.should_see_title_subtitle(
        UPDATE_TITLE_DATASOURCE, UPDATE_SUBTITLE_DATASOURCE
    )
    edit_page.selector.should_see_disabled_multiselect(PROJECT)
    edit_page.should_see_disabled_name_input(datasource.name)
    edit_page.should_see_save_reindex_button()


@pytest.mark.datasource
@pytest.mark.ui
def test_edit_file_datasource(page, datasource_utils):
    """Test that all main Edit Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    edit_page = CreateEditDatasourcePage(page)

    datasource = datasource_utils.create_file_datasource(
        files=[str(FILES_PATH / "test.txt")],
    )

    datasource_page.navigate_to()
    datasource_page.should_see_table_row_with_values(
        name=datasource.name,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.FILE,
        created_by=TEST_USER,
    )

    datasource_page.open_row_action_menu(datasource.name)
    datasource_page.should_see_edit_dropdown_values()
    datasource_page.click_row_action("Edit")

    edit_page.sidebar.should_see_title_subtitle(
        UPDATE_TITLE_DATASOURCE, UPDATE_SUBTITLE_DATASOURCE
    )
    edit_page.selector.should_see_disabled_multiselect(PROJECT)
    edit_page.should_see_disabled_name_input(datasource.name)


@pytest.mark.datasource
@pytest.mark.ui
def test_edit_google_datasource(page, datasource_utils):
    """Test that all main Edit Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    edit_page = CreateEditDatasourcePage(page)

    datasource = datasource_utils.create_google_doc_datasource(
        google_doc=GOOGLE_DOC_URL
    )

    datasource_page.navigate_to()
    datasource_page.should_see_table_row_with_values(
        name=datasource.name,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.GOOGLE,
        created_by=TEST_USER,
    )

    datasource_page.open_row_action_menu(datasource.name)
    datasource_page.should_see_edit_dropdown_values()
    datasource_page.should_see_edit_dropdown_full_reindex_value()
    datasource_page.click_row_action("Edit")

    edit_page.sidebar.should_see_title_subtitle(
        UPDATE_TITLE_DATASOURCE, UPDATE_SUBTITLE_DATASOURCE
    )
    edit_page.selector.should_see_disabled_multiselect(PROJECT)
    edit_page.should_see_disabled_name_input(datasource.name)
    edit_page.should_see_save_reindex_button()
