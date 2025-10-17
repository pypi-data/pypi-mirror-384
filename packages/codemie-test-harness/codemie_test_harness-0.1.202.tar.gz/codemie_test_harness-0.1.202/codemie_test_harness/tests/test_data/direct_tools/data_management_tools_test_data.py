import pytest

from codemie_test_harness.tests.enums.integrations import DataBaseDialect
from codemie_test_harness.tests.enums.tools import DataManagementTool, Toolkit
from codemie_test_harness.tests.utils.env_resolver import EnvironmentResolver

ELASTIC_TOOL_TASK = {
    "index": "_all",
    "query": '{"query": {"prefix": {"_index": "codemie"}}}',
}

sql_tools_test_data = [
    (
        Toolkit.DATA_MANAGEMENT,
        DataManagementTool.SQL,
        DataBaseDialect.MY_SQL,
        {"sql_query": "SHOW TABLES"},
        [{"Tables_in_my_database": "products"}, {"Tables_in_my_database": "users"}],
    ),
    (
        Toolkit.DATA_MANAGEMENT,
        DataManagementTool.SQL,
        DataBaseDialect.POSTGRES,
        {
            "sql_query": "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
        },
        [{"table_name": "users"}, {"table_name": "products"}],
    ),
    pytest.param(
        Toolkit.DATA_MANAGEMENT,
        DataManagementTool.SQL,
        DataBaseDialect.MS_SQL,
        {
            "sql_query": """SELECT table_name
                            FROM
                            information_schema.tables
                            WHERE
                            table_type = 'BASE TABLE'
                            AND
                            table_catalog = 'autotests'
                            AND
                            table_schema = 'dbo';
                            """
        },
        [{"table_name": "Users"}, {"table_name": "Products"}],
        marks=pytest.mark.skipif(
            not EnvironmentResolver.is_sandbox(),
            reason="MS SQL is only available in sandbox environments",
        ),
        id=DataBaseDialect.MS_SQL,
    ),
]

INFLUXDB_QUERY = {
    "sql_query": """
        from(bucket: "primary")
            |> range(start: 2025-09-01T00:00:00Z, stop: 2025-10-01T00:00:00Z)
            |> filter(fn: (r) => r._measurement == "server_performance" and r.hostname == "api-gateway-01")
    """
}

RESPONSE_FOR_INFLUXDB = """
      "_value":89.9,
      "_field":"cpu_load_percent",
      "_measurement":"server_performance",
      "hostname":"api-gateway-01",
      "region":"us-east-1",
      "service":"api"
"""
