from codemie_test_harness.tests.enums.tools import Toolkit, ReportPortalTool

rp_test_data = [
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_EXTENDED_LAUNCH_DATA_AS_RAW,
        "Get details for the launch with ID 23 in a raw HTML format. If content exceeds the token limit for display show truncated version",
        """
        The launch with ID 23 has been successfully retrieved in HTML format. Here is the raw HTML content for your reference:

       ```html
       <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
       <html>
       <head>
         <title></title>
         <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
         <style type="text/css">
           a {text-decoration: none}
         </style>
       </head>
       <body text="#000000" link="#000000" alink="#000000" vlink="#000000">
       <table role="none" width="100%" cellpadding="0" cellspacing="0" border="0">
       <tr>
           <td width="50%">&nbsp;</td><td align="center">
           <table id="JR_PAGE_ANCHOR_0_1" role="none" class="jrPage" data-jr-height="57605" cellpadding="0" cellspacing="0" border="0" style="empty-cells: show; width: 842px; border-collapse: collapse;">
             <style type="text/css">
             #JR_PAGE_ANCHOR_0_1 th {font-weight: normal;}
             #JR_PAGE_ANCHOR_0_1 ul {list-style-type: disc; padding-inline-start: 40px; margin: 0px;}
             #JR_PAGE_ANCHOR_0_1 ol {list-style-type: decimal; padding-inline-start: 40px; margin: 0px;}
           </style>
           <tr role="none" valign="top" style="height:0">
           <td style="width:20px"></td>
           <!-- Additional table cells with widths defined -->
           </tr>
           <tr valign="top" style="height:20px">
           <td colspan="26">
           <!-- Detailed information about the launch -->
           </td>
           </tr>
           <!-- Additional rows containing more detailed information about steps, types, and statistics -->
           </table>
       </td>
       </tr>
       <tr>
           <td width="50%">&nbsp;</td>
       </tr>
       </table>
       </body>
       </html>
       ```
       This HTML document contains structured details about the launch, including metadata, statistics, and step-by-step information.
        If you need to reformat the data or extract specific information, please let me know how I can assist further!,
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_LAUNCH_DETAILS,
        "Get details about launch with ID 23",
        """
        Launch Details: Pytest Regression (Launch 2)
        Overview
        ID: 23
        Name: Pytest Regression
        Number: 2
        Status: STOPPED
        Owner: anton_yeromin
        Environment: azure
        Timing Information
        Start Time: September 8, 2025, 08:46:01
        End Time: September 8, 2025, 09:11:14
        Duration: ~25 minutes
        Test Execution Statistics
        Total Tests: 888
        Passed: 743 (83.7%)
        Failed: 4 (0.5%)
        Skipped: 141 (15.9%)
        Defect Information
        To Investigate: 145 issues
        This launch appears to have been manually stopped, as indicated by its status and description.
        Despite being stopped, it shows a good pass rate of 83.7%, with only 4 failed tests.
        However, there are 145 items marked as "to investigate" which might require attention.
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_ALL_LAUNCHES,
        "Get all launches for env:preview and return just the number of launches found",
        "There are **15** launches found for the environment `preview`.",
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.FIND_TEST_ITEM_BY_ID,
        "Get test item by ID 111487",
        """
            Here are the details for the test item with ID **111487**:
            
            - **Name**: `codemie_test_harness/tests/assistant/tools/plugin/test_assistant_with_plugin_and_mcp_servers.py::test_assistant_with_plugin_and_cli_mcp_server[ls]`
            - **Code Reference**: `codemie_test_harness/tests/assistant/tools/plugin/test_assistant_with_plugin_and_mcp_servers.py:test_assistant_with_plugin_and_cli_mcp_server`
            
            ### Parameters
            - **prompt**: `ls`
            - **expected_response**: 
              ```
              Here is a list of files and directories in `/apps/codemie-sdk/test-harness/codemie_test_harness/tests`:
            
              - Files:
                - `.DS_Store`
                - `__init__.py`
                - `conftest.py`
            
              - Directories:
                - `__pycache__`
                - `assistant`
                - `e2e`
                - `enums`
                - `integrations`
                - `llm`
                - `providers`
                - `search`
                - `service`
                - `test_data`
                - `ui`
                - `utils`
                - `workflow`
              ```
            
            ### Attributes
            - **plugin**
            - **assistant**
            - **api**
            - **mcp**
            
            ### Status
            - **Start Time**: October 8, 2025, 10:02:41 AM UTC
            - **End Time**: October 8, 2025, 10:05:09 AM UTC
            - **Status**: **FAILED**
            
            ### Execution Statistics
            - **Total Executions**: 1
            - **Failed Executions**: 1
            - **Defects**:
              - **To Investigate**: `ti001` (1 instance)
            
            ### Issue Details
            - **Issue Type**: `ti001`
            - **Auto Analyzed**: No
            - **Ignore Analyzer**: No
            
            ### Launch Information
            - **Launch Name**: Pytest Regression
            - **Launch Number**: 121
            - **Launch ID**: 321
            
            This test appears to have failed due to a defect marked for investigation. If you need further insights or actions, please let me know!
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_TEST_ITEMS_FOR_LAUNCH,
        "Get test items for launch ID 23",
        """
        Here are some test items for launch ID 23:
       
       1. **Test Item:** `test_cli_mcp_server[cat file.txt]`
          - **File:** `codemie_test_harness/tests/assistant/tools/mcp/test_cli_mcp_server.py`
         - **Status:** PASSED
          - **Attributes:** Regression, MCP
          - **Start Time:** 2025-09-08T08:46:34.564Z
          - **End Time:** 2025-09-08T08:46:41.799Z
       
       2. **Test Item:** `test_create_assistant_and_prompt_with_file[test.csv]`
          - **File:** `codemie_test_harness/tests/assistant/test_assistants.py`
          - **Status:** PASSED
          - **Attributes:** Regression, Smoke, Testcase EPMCDME-4001, EPMCDME-4002, EPMCDME-2527
          - **Start Time:** 2025-09-08T08:46:34.565Z
         - **End Time:** 2025-09-08T08:46:50.522Z
       
       3. **Test Item:** `test_assistant_with_codebase_tools[Toolkit.CODEBASE_TOOLS_CodeBaseTool.SEARCH_CODE_REPO_V2]`
          - **File:** `codemie_test_harness/tests/assistant/tools/codebase/test_codebase_tools.py`
          - **Status:** PASSED
          - **Attributes:** Regression
          - **Start Time:** 2025-09-08T08:46:34.566Z
          - **End Time:** 2025-09-08T08:47:21.503Z
       
       4. **Test Item:** `test_edit_description_for_file_datasource`
          - **File:** `codemie_test_harness/tests/assistant/datasource/test_file_indexing.py`
          - **Status:** PASSED
          - **Attributes:** Regression, Smoke
          - **Start Time:** 2025-09-08T08:46:34.606Z
          - **End Time:** 2025-09-08T08:46:41.655Z
       
       5. **Test Item:** `test_create_assistant_with_file_datasource[gecko-test.ini]`
          - **File:** `codemie_test_harness/tests/assistant/datasource/test_file_indexing.py`
          - **Status:** SKIPPED
          - **Attributes:** Regression, Smoke
          - **Start Time:** 2025-09-08T08:46:34.564Z
          - **End Time:** 2025-09-08T08:46:34.627Z
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_LOGS_FOR_TEST_ITEM,
        "Get first page of the logs for test item ID 111487",
        """
            Here are the logs from the first page for test item ID 111487:
            
            | Time                          | Level  | Message                                                                                                                   |
            |-------------------------------|--------|---------------------------------------------------------------------------------------------------------------------------|
            | 2025-10-08T10:02:41.368Z      | DEBUG  | Starting new HTTPS connection (1): keycloak.eks-core.aws.main.edp.projects.epam.com:443                                    |
            | 2025-10-08T10:02:41.647Z      | DEBUG  | https://keycloak.eks-core.aws.main.edp.projects.epam.com:443 "POST /auth/realms/codemie-prod/protocol/openid-connect/token HTTP/1.1" 200 2500 |
            | 2025-10-08T10:02:41.651Z      | INFO   | Plugin key: f6455cc5-af78-4420-86a9-965ac6f0425e                                                                           |
            | 2025-10-08T10:02:41.652Z      | DEBUG  | Making /v1/settings/project request to https://codemie-preview.lab.epam.com/code-assistant-api<class 'dict'>                  |
            | 2025-10-08T10:02:41.652Z      | DEBUG  | Request body: {'project_name': 'codemie', 'alias': 'cfs_qlbpwnkmgoqgkcc', 'default': False, 'is_global': False, 'credential_type': <CredentialTypes.PLUGIN: 'Plugin'>, 'credential_values': [{'key': 'url', 'value': 'AUTO_GENERATED'}, {'key': 'plugin_key', 'value': 'f6455cc5-af78-4420-86a9-965ac6f0425e'}], 'setting_type': <IntegrationType.PROJECT: 'project'>} |
            | 2025-10-08T10:02:41.653Z      | DEBUG  | Starting new HTTPS connection (1): codemie-preview.lab.epam.com:443                                                        |
            | 2025-10-08T10:02:42.051Z      | DEBUG  | https://codemie-preview.lab.epam.com:443 "POST /code-assistant-api/v1/settings/project HTTP/1.1" 200 41                     |
            | 2025-10-08T10:02:42.052Z      | DEBUG  | Received response with status 200                                                                                           |
            | 2025-10-08T10:02:42.052Z      | DEBUG  | Response datasource_type: <class 'dict'>                                                                                    |
            | 2025-10-08T10:02:42.060Z      | INFO   | Successfully processed /v1/settings/project request to <class 'dict'>                                                       |
            | 2025-10-08T10:02:42.060Z      | DEBUG  | Making /v1/settings/project request to https://codemie-preview.lab.epam.com/code-assistant-apityping.List[codemie_sdk.models.integration.Integration]            |
            | 2025-10-08T10:02:42.061Z      | DEBUG  | Request params: {'page': 0, 'per_page': 200}                                                                               |
            | 2025-10-08T10:02:42.062Z      | DEBUG  | Starting new HTTPS connection (1): codemie-preview.lab.epam.com:443                                                        |
            | 2025-10-08T10:02:42.562Z      | DEBUG  | https://codemie-preview.lab.epam.com:443 "GET /code-assistant-api/v1/settings/project?page=0&per_page=200 HTTP/1.1" 200 93345 |
            | 2025-10-08T10:02:42.573Z      | DEBUG  | Received response with status 200                                                                                           |
            | 2025-10-08T10:02:42.573Z      | DEBUG  | Response datasource_type: <class 'dict'>                                                                                    |
            | 2025-10-08T10:02:42.585Z      | INFO   | Successfully processed /v1/settings/project request to typing.List[codemie_sdk.models.integration.Integration]                |
            | 2025-10-08T10:02:42.647Z      | DEBUG  | Making /v1/settings/project request to https://codemie-preview.lab.epam.com/code-assistant-apityping.List[codemie_sdk.models.integration.Integration]            |
            | 2025-10-08T10:02:42.647Z      | DEBUG  | Request params: {'page': 0, 'per_page': 200}                                                                               |
            | 2025-10-08T10:02:42.649Z      | DEBUG  | Starting new HTTPS connection (1): codemie-preview.lab.epam.com:443                                                        |
            
            If you need additional pages of logs, please let me know.
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_USER_INFORMATION,
        "Get user information from reportal with username anton_yeromin",
        """
        User Information: Anton Yeromin
        Personal Details
        Full Name: Anton Yeromin
        Email: anton_yeromin@epam.com
        Username: anton_yeromin
        User ID: 4
        Account Type: SAML
        Role: USER
        Status: Active
        Photo: Loaded
        Login Information
        Last Login: September 9, 2025
        Synchronization Date: September 8, 2025
        Project Assignments
        EPM-CDME Project
        Project ID: 4
        Role: PROJECT_MANAGER
        Entry Type: INTERNAL
        Personal Project
        Project ID: 6
        Name: anton_yeromin_personal
        Role: PROJECT_MANAGER
        Entry Type: PERSONAL
        This user has project management responsibilities in both an internal project (EPM-CDME) and their personal project space.
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_DASHBOARD_DATA,
        "Get dashboard data from report portal where ID = 2",
        """
        Dashboard Details: test-dashboard
        I was able to retrieve the dashboard data for ID 2:
        Dashboard Information
        ID: 2
        Name: test-dashboard
        Owner: dmytro_adamtsev
        Description: dashboard for testing purposes
        Dashboard Content
        This dashboard does not contain any widgets. 
        It appears to be an empty dashboard that was likely created for testing purposes, as suggested by its name and description.
        """,
    ),
]
