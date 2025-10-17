import pytest

from codemie_test_harness.tests import PROJECT, TEST_USER
from codemie_test_harness.tests.test_data.google_datasource_test_data import (
    GOOGLE_DOC_URL,
)
from codemie_test_harness.tests.ui.pageobject.datasources.datasource_page import (
    DataSourcePage,
)
from codemie_test_harness.tests.ui.pageobject.datasources.view_datasource_page import (
    ViewDatasourcePage,
)
from codemie_test_harness.tests.ui.test_data.datasource_test_data import (
    TITLE_VIEW_DATASOURCE,
    SUBTITLE_VIEW_DATASOURCE,
    DataSourceStatus,
    DataSourceType,
    DataSourceFilterType,
)
from codemie_test_harness.tests.utils.constants import FILES_PATH


@pytest.mark.datasource
@pytest.mark.ui
def test_view_git_datasource_page(
    page, datasource_utils, git_integration, default_embedding_llm, client
):
    """Test that all main View Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    view_page = ViewDatasourcePage(page)
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

    datasource_page.click_datasource_row_by_name(datasource.name)
    view_page.sidebar.should_see_title_subtitle(
        TITLE_VIEW_DATASOURCE, SUBTITLE_VIEW_DATASOURCE
    )
    view_page.should_see_ds_name_and_owner(
        datasource_name=datasource.name, owner=TEST_USER
    )
    view_page.should_see_description(description=datasource.description)
    view_page.should_see_processing_summary(is_git=True)
    view_page.should_see_overview(
        project=PROJECT, ds_type=DataSourceType.GIT, ds_id=datasource.id
    )
    view_page.should_see_configuration(
        embeddings_model=default_embedding_llm.label,
        summarization_model=client.llms.list()[3].label,
    )
    view_page.should_open_and_see_processed_data()


@pytest.mark.datasource
@pytest.mark.ui
def test_view_confluence_datasource_page(
    page, datasource_utils, confluence_integration, default_embedding_llm, client
):
    """Test that all main View Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    view_page = ViewDatasourcePage(page)
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

    datasource_page.click_datasource_row_by_name(datasource.name)
    view_page.sidebar.should_see_title_subtitle(
        TITLE_VIEW_DATASOURCE, SUBTITLE_VIEW_DATASOURCE
    )
    view_page.should_see_ds_name_and_owner(
        datasource_name=datasource.name, owner=TEST_USER
    )
    view_page.should_see_description(description=datasource.description)
    view_page.should_see_processing_summary()
    view_page.should_see_overview(
        project=PROJECT, ds_type=DataSourceFilterType.CONFLUENCE, ds_id=datasource.id
    )
    view_page.should_see_configuration(
        embeddings_model=default_embedding_llm.label,
        summarization_model=client.llms.list()[3].label,
    )
    view_page.should_see_processed_data()


@pytest.mark.datasource
@pytest.mark.ui
def test_view_jira_datasource_page(
    page, datasource_utils, jira_integration, default_embedding_llm, client
):
    """Test that all main View Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    view_page = ViewDatasourcePage(page)
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

    datasource_page.click_datasource_row_by_name(datasource.name)
    view_page.sidebar.should_see_title_subtitle(
        TITLE_VIEW_DATASOURCE, SUBTITLE_VIEW_DATASOURCE
    )
    view_page.should_see_ds_name_and_owner(
        datasource_name=datasource.name, owner=TEST_USER
    )
    view_page.should_see_description(description=datasource.description)
    view_page.should_see_processing_summary()
    view_page.should_see_overview(
        project=PROJECT, ds_type=DataSourceFilterType.JIRA, ds_id=datasource.id
    )
    view_page.should_see_configuration(
        embeddings_model=default_embedding_llm.label,
        summarization_model=client.llms.list()[3].label,
    )
    view_page.should_see_processed_data()


@pytest.mark.datasource
@pytest.mark.ui
def test_view_file_datasource_page(
    page, datasource_utils, default_embedding_llm, client
):
    """Test that all main View Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    view_page = ViewDatasourcePage(page)
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

    datasource_page.click_datasource_row_by_name(datasource.name)
    view_page.sidebar.should_see_title_subtitle(
        TITLE_VIEW_DATASOURCE, SUBTITLE_VIEW_DATASOURCE
    )
    view_page.should_see_ds_name_and_owner(
        datasource_name=datasource.name, owner=TEST_USER
    )
    view_page.should_see_description(description=datasource.description)
    view_page.should_see_processing_summary()
    view_page.should_see_overview(
        project=PROJECT, ds_type=DataSourceFilterType.FILE, ds_id=datasource.id
    )
    view_page.should_see_configuration(
        embeddings_model=default_embedding_llm.label,
        summarization_model=client.llms.list()[3].label,
    )
    view_page.should_see_processed_data()


@pytest.mark.datasource
@pytest.mark.ui
def test_view_google_datasource_page(
    page, datasource_utils, default_embedding_llm, client
):
    """Test that all main View Datasource page elements are visible."""
    datasource_page = DataSourcePage(page)
    view_page = ViewDatasourcePage(page)
    datasource = datasource_utils.create_google_doc_datasource(
        google_doc=GOOGLE_DOC_URL,
    )

    datasource_page.navigate_to()
    datasource_page.should_see_table_row_with_values(
        name=datasource.name,
        status=DataSourceStatus.COMPLETED,
        project=PROJECT,
        type_=DataSourceFilterType.GOOGLE,
        created_by=TEST_USER,
    )

    datasource_page.click_datasource_row_by_name(datasource.name)
    view_page.sidebar.should_see_title_subtitle(
        TITLE_VIEW_DATASOURCE, SUBTITLE_VIEW_DATASOURCE
    )
    view_page.should_see_ds_name_and_owner(
        datasource_name=datasource.name, owner=TEST_USER
    )
    view_page.should_see_description(description=datasource.description)
    view_page.should_see_processing_summary()
    view_page.should_see_overview(
        project=PROJECT, ds_type=DataSourceFilterType.GOOGLE, ds_id=datasource.id
    )
    view_page.should_see_configuration(
        embeddings_model=default_embedding_llm.label,
        summarization_model=client.llms.list()[3].label,
    )
    view_page.should_see_processed_data()
