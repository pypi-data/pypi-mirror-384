import pytest

from codemie_test_harness.tests.enums.integrations import DataBaseDialect
from codemie_test_harness.tests.utils.env_resolver import EnvironmentResolver

ELASTIC_TOOL_TASK = """
    send the query to Elastic:
    {'index': 'codemie-*', 'query': {'size': 0, 'aggs': {'indices': {'terms': {'field': '_index', 'size': 5, 'order': {'_count': 'asc'}}}}}}
    return only the number of failed from _shards node.
"""

RESPONSE_FOR_ELASTIC = """
    The query was executed successfully. The number of failed shards from the _shards node is 0.    
"""

SQL_TOOL_CREATE_TABLE_TASK = """
   Insert a new Employees table with Firstname, Lastname, Email, Department columns and fill it with 10 records
   
   Example for MySQL dialect:
   The first query to create table: {'sql_query': 'CREATE TABLE Employees ( 
    EmployeeID INT AUTO_INCREMENT PRIMARY KEY, 
    Firstname VARCHAR(50), 
    Lastname VARCHAR(50), 
    Email VARCHAR(100), 
    Department VARCHAR(50) 
    );'} 
    
    The second query to fill table: {'sql_query': "INSERT INTO Employees (Firstname, Lastname, Email, Department) VALUES 
    ('John', 'Doe', 'john.doe@example.com', 'Engineering'), 
    ('Jane', 'Smith', 'jane.smith@example.com', 'Marketing'), 
    ('Jim', 'Brown', 'jim.brown@example.com', 'Sales'), 
    ('Lucy', 'Adams', 'lucy.adams@example.com', 'Finance'), 
    ('Michael', 'Johnson', 'michael.johnson@example.com', 'Engineering'), 
    ('Lisa', 'White', 'lisa.white@example.com', 'Human Resources'), 
    ('Adam', 'Young', 'adam.young@example.com', 'IT'), 
    ('Nancy', 'Green', 'nancy.green@example.com', 'Customer Support'), 
    ('Frank', 'Thomas', 'frank.thomas@example.com', 'Operations'), 
    ('Anna', 'King', 'anna.king@example.com', 'Research');"} 
   
"""
SQL_TOOL_INSERT_TABLE_TASK = "Add new Employee: Sarah Connor sarah.connor@email.com from Security department. Employees table has the following columns: Firstname, Lastname, Email, Department."

SQL_TOOL_QUERY_TABLE_TASK = "SELECT * FROM Employees WHERE department = 'Security'"
SQL_TOOL_DELETE_TABLE_TASK = "Delete Employees table."

RESPONSE_FOR_SQL = """
    Here is the list of employees from the Security department:

    | First Name | Last Name | Email                   | Department |
    |------------|-----------|-------------------------|------------|
    | Sarah      | Connor    | sarah.connor@email.com  | Security   |
"""

# Define test data for SQL tools based on environment
sql_tools_test_data = [
    DataBaseDialect.MY_SQL,
    DataBaseDialect.POSTGRES,
    pytest.param(
        DataBaseDialect.MS_SQL,
        marks=pytest.mark.skipif(
            not EnvironmentResolver.is_sandbox(),
            reason="MS SQL is only available in staging environments",
        ),
        id=DataBaseDialect.MS_SQL,
    ),
]

# InfluxDB-specific task
INFLUXDB_QUERY_MEASUREMENT_TASK = """
    Execute the query:
    'from(bucket: "primary") 
     |> range(start: 2025-09-01T00:00:00Z, stop: 2025-10-01T00:00:00Z) 
     |> filter(fn: (r) => r._measurement == "server_performance" and r.hostname == "api-gateway-01")'
    Output format is a table:
    | time | host | region | cpu_load | memory_usage |
    Do not summarize the output!
    """

RESPONSE_FOR_INFLUXDB = """

    time    |	host    |	region	    |   cpu_load    |	memory_usage
2025-09-16T02:00:05Z	|   api-gateway-01  |	us-east-1	|   45.8    |	8.5
2025-09-16T02:00:20Z	|   api-gateway-01  |   us-east-1   |	89.9    |	14.8
"""
