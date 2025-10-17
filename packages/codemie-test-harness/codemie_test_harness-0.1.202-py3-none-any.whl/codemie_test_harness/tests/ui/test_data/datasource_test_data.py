"""
Test Data for Data Source UI – used for parametrized testing and test validation
"""

from enum import Enum


# ==================== ENUMS ====================
class DataSourceFilterType(str, Enum):
    CODE = "Code"
    CONFLUENCE = "Confluence"
    JIRA = "Jira"
    FILE = "File"
    GOOGLE = "Google"
    PROVIDER = "Provider"

    def __str__(self):
        return self.value


class DataSourceType(str, Enum):
    GIT = "Git"
    CONFLUENCE = "Confluence"
    JIRA = "Jira"
    FILE = "File"
    GOOGLE = "Google"

    def __str__(self):
        return self.value


class DataSourceFilterStatus(str, Enum):
    COMPLETED = "Completed"
    FAILED = "Failed"
    IN_PROGRESS = "In Progress"

    def __str__(self):
        return self.value


class DataSourceStatus(str, Enum):
    COMPLETED = "Completed"
    ERROR = "Error"
    FETCHING = "Fetching"

    def __str__(self):
        return self.value


class SummarizationMethod(str, Enum):
    WHOLE_CODEBASE = "Whole Codebase"
    PER_FILE = "Summarization per file"
    PER_CHUNKS = "Summarization per chunks"

    def __str__(self):
        return self.value


class EmbeddingModel(str, Enum):
    ADA = "Text Embedding Ada"
    GECKO = "Text Embedding Gecko"
    TITAN_V2 = "Titan Embed Text v2.0"

    def __str__(self):
        return self.value


class DataSourceColumnName(str, Enum):
    NAME = "Name"
    PROJECT = "Project"
    TYPE = "Type"
    CREATED_BY = "Created By"
    CREATED = "Created"
    UPDATED = "Updated"
    SHARED = "Shared"
    STATUS = "Status"
    ACTIONS = "Actions"

    def __str__(self):
        return self.value


# ==================== CONSTANTS ====================

DATA_SOURCE_FILTER_TYPES_LIST = [t for t in DataSourceFilterType]
DATA_SOURCE_TYPES_LIST = [t for t in DataSourceType]
DATA_SOURCE_FILTER_STATUSES_LIST = [s for s in DataSourceFilterStatus]
DATA_SOURCE_STATUSES_LIST = [s for s in DataSourceStatus]
DATAS_SOURCE_COLUMN_LIST = [c for c in DataSourceColumnName]
SUMMARIZATION_METHODS_LIST = [m for m in SummarizationMethod]
EMBEDDING_MODELS_LIST = [m for m in EmbeddingModel]

PROJECT_LABEL = "Project"
STATUS_LABEL = "Status"

MAIN_TITLE_DATASOURCE = "Data Sources"
MAIN_SUBTITLE_DATASOURCE = "Connect and manage your data sources in one place"
TITLE_CREATE_DATASOURCE = "New DataSource"
SUBTITLE_CREATE_DATASOURCE = "Start indexing your data source"
TITLE_VIEW_DATASOURCE = "View DataSource"
SUBTITLE_VIEW_DATASOURCE = "View your data source datails"
UPDATE_TITLE_DATASOURCE = "Update DataSource"
UPDATE_SUBTITLE_DATASOURCE = "Update your data source and start re-indexing"

FILE_INSTRUCTIONS = (
    "Max size: 100Mb. Formats: .yml, .yaml, .json, .pptx, .csv, .txt, "
    ".pdf, .docx, .xlsx, .xml"
)
GOOGLE_INSTRUCTIONS = (
    "Please ensure your Google document is properly formatted and shared with the"
    " service account. For detailed instructions, refer to the Guide"
)
GOOGLE_EXAMPLE = "Google documents must follow a specific format for LLM routing: View Format Example"

EMPTY_NAME_ERROR = "Data source name is required"
EMPTY_DESCRIPTION_ERROR = "description is a required field"
EMPTY_REPO_LINK_ERROR = "Repo Link is required"
EMPTY_BRANCH_ERROR = "Branch is required"
EMPTY_CQL_ERROR = "cql is a required field"
EMPTY_JQL_ERROR = "jql is a required field"
EMPTY_FILE_ERROR = (
    "Invalid file type found, only .yml, .yaml, .json, .pptx, .csv, .txt, .pdf, "
    ".docx, .xlsx, .xml are allowed"
)
EMPTY_GOOGLE_LINK_ERROR = "Google Docs link is required"
