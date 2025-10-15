import pytest

from codemie_test_harness.tests import TEST_USER
from codemie_test_harness.tests.ui.pageobject.datasources.datasource_page import (
    DataSourcePage,
)
from codemie_test_harness.tests.ui.test_data.datasource_test_data import (
    MAIN_TITLE_DATASOURCE,
    MAIN_SUBTITLE_DATASOURCE,
)
from codemie_test_harness.tests.utils.base_utils import get_random_name


@pytest.mark.datasource
@pytest.mark.ui
def test_datasource_sidebar_interaction(page):
    """Test sidebar filters interactions."""
    search_input = get_random_name()
    datasource_page = DataSourcePage(page)

    datasource_page.navigate_to()
    datasource_page.sidebar.should_see_title_subtitle(
        MAIN_TITLE_DATASOURCE, MAIN_SUBTITLE_DATASOURCE
    )
    datasource_page.sidebar.input_data_search(search_input).should_see_search_input(
        search_input
    )
    datasource_page.sidebar.should_see_selected_checkboxes()
    datasource_page.sidebar.toggle_created_by_me().should_see_created_by_me_value(
        TEST_USER
    )
    datasource_page.sidebar.should_see_project_filter()
    datasource_page.sidebar.should_see_status_dropdown()
    datasource_page.sidebar.should_select_status_dropdown()
    datasource_page.sidebar.click_clear_all_button().should_see_cleared_filters()


@pytest.mark.datasource
@pytest.mark.ui
def test_datasource_sidebar_hiding_elements(page):
    """Test sidebar filters hiding."""
    datasource_page = DataSourcePage(page)

    datasource_page.navigate_to()
    datasource_page.sidebar.click_type_filter_hide_button().should_not_see_type_filters()
    datasource_page.sidebar.click_project_filter_hide_button().should_not_see_project_filters()
    datasource_page.sidebar.click_created_by_filter_hide_button().should_not_see_created_by_filters()
    datasource_page.sidebar.click_status_filter_hide_button().should_not_see_status_filters()


@pytest.mark.datasource
@pytest.mark.ui
def test_datasource_page_elements_visibility(page):
    """Test DataSource index page and sidebar elements are visible."""
    datasource_page = DataSourcePage(page)

    datasource_page.navigate_to()
    datasource_page.should_see_create_datasource_button()
    datasource_page.should_see_table_rows(minimum_count=10)
    datasource_page.should_see_table_column_names()
    datasource_page.should_see_pagination()
