from codemie_test_harness.tests.enums.tools import Toolkit, ReportPortalTool

report_portal_tools_test_data = [
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_LAUNCH_DETAILS,
        {"launch_id": "23"},
        """
        {
            "owner": "anton_yeromin",
            "description": "stopped",
            "id": 23,
            "uuid": "05e770ed-4b9d-43c3-acf2-43a50e7875dc",
            "name": "Pytest Regression",
            "number": 2,
            "startTime": "2025-09-08T08:46:01.157Z",
            "endTime": "2025-09-08T09:11:14.987Z",
            "lastModified": "2025-09-08T09:11:15.196270Z",
            "status": "STOPPED",
            "statistics": {
                "executions": {
                    "total": 888,
                    "failed": 4,
                    "passed": 743,
                    "skipped": 141
                },
                "defects": {
                    "to_investigate": {
                        "total": 145,
                        "ti001": 145
                    }
                }
            },
            "attributes": [
                {
                    "key": "status",
                    "value": "stopped"
                },
                {
                    "key": "env",
                    "value": "azure"
                }
            ],
            "mode": "DEFAULT",
            "analysing": [],
            "approximateDuration": 0.0,
            "hasRetries": false,
            "rerun": false,
            "metadata": {
                "rp.cluster.lastRun": "1757322678794"
            },
            "retentionPolicy": "REGULAR"
        },
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_ALL_LAUNCHES,
        {"page_number": 1},
        """
        {
            "content": [
                {
                    "owner": "anton_yeromin",
                    "description": "stopped",
                    "id": 22,
                    "uuid": "038c493c-b9bf-405f-b1b1-7842ffe5de9a",
                    "name": "Pytest Regression",
                    "number": 1,
                    "startTime": "2025-09-08T08:17:26.906Z",
                    "endTime": "2025-09-08T08:46:23.541Z",
                    "lastModified": "2025-09-08T08:46:23.826436Z",
                    "status": "STOPPED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "failed": 19,
                            "passed": 728,
                            "skipped": 141
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 160,
                                "ti001": 160
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "status",
                            "value": "stopped"
                        },
                        {
                            "key": "env",
                            "value": "azure"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 0.0,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757321194743"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "description": "stopped",
                    "id": 23,
                    "uuid": "05e770ed-4b9d-43c3-acf2-43a50e7875dc",
                    "name": "Pytest Regression",
                    "number": 2,
                    "startTime": "2025-09-08T08:46:01.157Z",
                    "endTime": "2025-09-08T09:11:14.987Z",
                    "lastModified": "2025-09-08T09:11:15.196270Z",
                    "status": "STOPPED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "failed": 4,
                            "passed": 743,
                            "skipped": 141
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 145,
                                "ti001": 145
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "status",
                            "value": "stopped"
                        },
                        {
                            "key": "env",
                            "value": "azure"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 0.0,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757322678794"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 25,
                    "uuid": "b1580190-ddd7-4496-9904-61f140665a65",
                    "name": "Pytest Regression",
                    "number": 4,
                    "startTime": "2025-09-08T11:49:50.308Z",
                    "endTime": "2025-09-08T12:06:25.438Z",
                    "lastModified": "2025-09-08T12:06:25.540618Z",
                    "status": "FAILED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "passed": 846,
                            "skipped": 42
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 42,
                                "ti001": 42
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "preview"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 3202.146,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757333186074"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "description": "stopped",
                    "id": 26,
                    "uuid": "4b9b9d74-dd07-4ddf-a6cb-f1450bfacd9e",
                    "name": "Pytest Regression",
                    "number": 5,
                    "startTime": "2025-09-08T12:43:08.988Z",
                    "endTime": "2025-09-08T13:16:11.869Z",
                    "lastModified": "2025-09-08T13:16:12.022623Z",
                    "status": "STOPPED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "failed": 3,
                            "passed": 744,
                            "skipped": 141
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 144,
                                "ti001": 144
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "status",
                            "value": "stopped"
                        },
                        {
                            "key": "env",
                            "value": "azure"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 995.13,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757337373405"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "description": "stopped",
                    "id": 27,
                    "uuid": "22d20d4a-004f-4286-a630-5baa59a4aeff",
                    "name": "Pytest Regression",
                    "number": 6,
                    "startTime": "2025-09-08T13:50:57.368Z",
                    "endTime": "2025-09-08T13:52:37.258Z",
                    "lastModified": "2025-09-08T13:52:39.860832Z",
                    "status": "STOPPED",
                    "statistics": {
                        "executions": {
                            "total": 15,
                            "passed": 1,
                            "failed": 14
                        },
                        "defects": {}
                    },
                    "attributes": [
                        {
                            "key": "status",
                            "value": "stopped"
                        },
                        {
                            "key": "env",
                            "value": "preview"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 995.13,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757339559884"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 28,
                    "uuid": "95ec670d-2252-42a3-8250-a028dcce8176",
                    "name": "Pytest Regression",
                    "number": 7,
                    "startTime": "2025-09-08T13:58:52.195Z",
                    "endTime": "2025-09-08T14:16:33.106Z",
                    "lastModified": "2025-09-08T14:16:33.172673Z",
                    "status": "FAILED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "failed": 3,
                            "passed": 843,
                            "skipped": 42
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 45,
                                "ti001": 45
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "preview"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 995.13,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757340994692"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 30,
                    "uuid": "f8cc3f1a-7582-46c2-b12e-0c20a3dbb9c5",
                    "name": "Pytest Regression",
                    "number": 8,
                    "startTime": "2025-09-08T15:00:41.161Z",
                    "endTime": "2025-09-08T15:17:26.672Z",
                    "lastModified": "2025-09-08T15:17:26.725642Z",
                    "status": "FAILED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "failed": 1,
                            "passed": 845,
                            "skipped": 42
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 43,
                                "ti001": 43
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "preview"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 1028.0205,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757344647421"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 31,
                    "uuid": "e441203d-40a6-4718-b365-67fbd6bf8b7c",
                    "name": "Pytest Regression",
                    "number": 9,
                    "startTime": "2025-09-09T06:36:31.663Z",
                    "endTime": "2025-09-09T09:55:07.390391Z",
                    "lastModified": "2025-09-09T09:55:07.396057Z",
                    "status": "INTERRUPTED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "passed": 770,
                            "failed": 8,
                            "skipped": 110
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 118,
                                "ti001": 118
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "aws"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 1020.517333,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757411732542"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 32,
                    "uuid": "dc344b53-b929-4b75-ab82-6cb61f04040d",
                    "name": "Pytest Regression",
                    "number": 10,
                    "startTime": "2025-09-09T06:38:19.683Z",
                    "endTime": "2025-09-09T09:55:07.395393Z",
                    "lastModified": "2025-09-09T09:55:07.396166Z",
                    "status": "INTERRUPTED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "passed": 300,
                            "failed": 447,
                            "skipped": 141
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 588,
                                "ti001": 588
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "azure"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 1020.517333,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757411824642"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 33,
                    "uuid": "a4052bd7-42f9-4486-86a6-fa662a8618b1",
                    "name": "Pytest Regression",
                    "number": 11,
                    "startTime": "2025-09-09T07:00:31.710Z",
                    "endTime": "2025-09-09T10:55:07.405340Z",
                    "lastModified": "2025-09-09T10:55:07.409351Z",
                    "status": "INTERRUPTED",
                    "statistics": {
                        "executions": {
                            "total": 79,
                            "passed": 5,
                            "failed": 55,
                            "skipped": 19
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 66,
                                "ti001": 66
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "azure"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 1020.517333,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757415316362"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 34,
                    "uuid": "4c967328-1dd3-4405-a117-dd5c66ad53a5",
                    "name": "Pytest Regression",
                    "number": 12,
                    "startTime": "2025-09-09T07:21:28.293Z",
                    "endTime": "2025-09-09T10:55:07.408322Z",
                    "lastModified": "2025-09-09T10:55:07.409535Z",
                    "status": "INTERRUPTED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "passed": 732,
                            "failed": 9,
                            "skipped": 147
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 156,
                                "ti001": 156
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "gcp"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 1020.517333,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757415319529"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 35,
                    "uuid": "56dd60de-0271-43b2-81be-5c0cfe3d847f",
                    "name": "Pytest Regression",
                    "number": 13,
                    "startTime": "2025-09-09T10:00:22.942Z",
                    "endTime": "2025-09-09T13:55:07.376388Z",
                    "lastModified": "2025-09-09T13:55:07.377003Z",
                    "status": "INTERRUPTED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "passed": 309,
                            "failed": 438,
                            "skipped": 141
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 579,
                                "ti001": 579
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "azure"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 1020.517333,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757426192463"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 36,
                    "uuid": "41420ab8-6039-452a-b408-c5f9299a43f1",
                    "name": "Pytest Regression",
                    "number": 14,
                    "startTime": "2025-09-09T10:01:06.439Z",
                    "endTime": "2025-09-09T10:40:03.279Z",
                    "lastModified": "2025-09-09T10:40:03.436937Z",
                    "status": "FAILED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "passed": 811,
                            "failed": 35,
                            "skipped": 42
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 77,
                                "ti001": 77
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "preview"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 1020.517333,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757414409362"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 38,
                    "uuid": "5c046800-d746-4b08-a8da-7e24f40d0048",
                    "name": "Pytest Regression",
                    "number": 15,
                    "startTime": "2025-09-09T15:00:20.775Z",
                    "endTime": "2025-09-09T18:55:07.379965Z",
                    "lastModified": "2025-09-09T18:55:07.380779Z",
                    "status": "INTERRUPTED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "passed": 730,
                            "failed": 17,
                            "skipped": 141
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 158,
                                "ti001": 158
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "azure"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 1349.598,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757444112042"
                    },
                    "retentionPolicy": "REGULAR"
                },
                {
                    "owner": "anton_yeromin",
                    "id": 39,
                    "uuid": "08368b09-5bf1-4c0f-bffa-189e316fca63",
                    "name": "Pytest Regression",
                    "number": 16,
                    "startTime": "2025-09-09T15:00:49.573Z",
                    "endTime": "2025-09-09T17:32:16.900Z",
                    "lastModified": "2025-09-09T17:32:17.018510Z",
                    "status": "FAILED",
                    "statistics": {
                        "executions": {
                            "total": 888,
                            "passed": 828,
                            "failed": 18,
                            "skipped": 42
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 60,
                                "ti001": 60
                            }
                        }
                    },
                    "attributes": [
                        {
                            "key": "env",
                            "value": "preview"
                        }
                    ],
                    "mode": "DEFAULT",
                    "analysing": [],
                    "approximateDuration": 1349.598,
                    "hasRetries": false,
                    "rerun": false,
                    "metadata": {
                        "rp.cluster.lastRun": "1757439142457"
                    },
                    "retentionPolicy": "REGULAR"
                }
            ],
            "page": {
                "number": 1,
                "size": 20,
                "totalElements": 15,
                "totalPages": 1
            }
        },
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.FIND_TEST_ITEM_BY_ID,
        {"item_id": "111487"},
        """
            {
              "id" : 111487,
              "uuid" : "ce9a949c-cc17-4869-b311-59d4955b5790",
              "name" : "codemie_test_harness/tests/assistant/tools/plugin/test_assistant_with_plugin_and_mcp_servers.py::test_assistant_with_plugin_and_cli_mcp_server[ls]",
              "codeRef" : "codemie_test_harness/tests/assistant/tools/plugin/test_assistant_with_plugin_and_mcp_servers.py:test_assistant_with_plugin_and_cli_mcp_server",
              "parameters" : [ {
                "key" : "prompt",
                "value" : "ls"
              }, {
                "key" : "expected_response",
                "value" : "\n            Here is a list of files and directories in `/apps/codemie-sdk/test-harness/codemie_test_harness/tests`:\n\n            - Files:\n              - `.DS_Store`\n              - `__init__.py`\n              - `conftest.py`\n\n            - Directories:\n              - `__pycache__`\n              - `assistant`\n              - `e2e`\n              - `enums`\n              - `integrations`\n              - `llm`\n              - `providers`\n              - `search`\n              - `service`\n              - `test_data`\n              - `ui`\n              - `utils`\n              - `workflow`\n        "
              } ],
              "attributes" : [ {
                "key" : null,
                "value" : "plugin"
              }, {
                "key" : null,
                "value" : "assistant"
              }, {
                "key" : null,
                "value" : "api"
              }, {
                "key" : null,
                "value" : "mcp"
              } ],
              "type" : "STEP",
              "startTime" : "2025-10-08T10:02:41.353Z",
              "endTime" : "2025-10-08T10:05:09.133Z",
              "status" : "FAILED",
              "statistics" : {
                "executions" : {
                  "total" : 1,
                  "failed" : 1
                },
                "defects" : {
                  "to_investigate" : {
                    "total" : 1,
                    "ti001" : 1
                  }
                }
              },
              "pathNames" : {
                "launchPathName" : {
                  "name" : "Pytest Regression",
                  "number" : 121
                }
              },
              "issue" : {
                "issueType" : "ti001",
                "autoAnalyzed" : false,
                "ignoreAnalyzer" : false,
                "externalSystemIssues" : [ ]
              },
              "hasChildren" : false,
              "hasStats" : true,
              "launchId" : 321,
              "uniqueId" : "auto:2b3f46b999e47da7019e17c19143373a",
              "testCaseId" : "codemie_test_harness/tests/assistant/tools/plugin/test_assistant_with_plugin_and_mcp_servers.py:test_assistant_with_plugin_and_cli_mcp_server[\n            Here is a list of files and directories in `/apps/codemie-sdk/test-harness/codemie_test_harness/tests`:\n\n            - Files:\n              - `.DS_Store`\n              - `__init__.py`\n              - `conftest.py`\n\n            - Directories:\n              - `__pycache__`\n              - `assistant`\n              - `e2e`\n              - `enums`\n              - `integrations`\n              - `llm`\n              - `providers`\n              - `search`\n              - `service`\n              - `test_data`\n              - `ui`\n              - `utils`\n              - `workflow`\n        ,ls]",
              "testCaseHash" : -1863961748,
              "patternTemplates" : [ ],
              "path" : "111487"
            }
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_TEST_ITEMS_FOR_LAUNCH,
        {"launch_id": "23", "page_number": 1, "status": "FAILED"},
        """
        {
            "content": [
                {
                    "id": 2884,
                    "uuid": "16617c14-babf-4c30-be17-30510d8d5073",
                    "name": "codemie_test_harness/tests/workflow/assistant_tools/ado/test_workflow_with_assistant_with_ado_test_plan_tools.py::test_workflow_with_assistant_with_ado_test_plan_tools",
                    "codeRef": "codemie_test_harness/tests/workflow/assistant_tools/ado/test_workflow_with_assistant_with_ado_test_plan_tools.py:test_workflow_with_assistant_with_ado_test_plan_tools",
                    "parameters": [],
                    "attributes": [
                        {
                            "key": "",
                            "value": "regression"
                        }
                    ],
                    "type": "STEP",
                    "startTime": "2025-09-08T08:51:45.158Z",
                    "endTime": "2025-09-08T08:52:54.202Z",
                    "status": "FAILED",
                    "statistics": {
                        "executions": {
                            "total": 1,
                            "failed": 1
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 1,
                                "ti001": 1
                            }
                        }
                    },
                    "pathNames": {
                        "launchPathName": {
                            "name": "Pytest Regression",
                            "number": 2
                        }
                    },
                    "issue": {
                        "issueType": "ti001",
                        "autoAnalyzed": false,
                        "ignoreAnalyzer": false,
                        "externalSystemIssues": []
                    },
                    "hasChildren": false,
                    "hasStats": true,
                    "launchId": 23,
                    "uniqueId": "auto:87331521821410ba6c28c2a3a9643eb7",
                    "testCaseId": "codemie_test_harness/tests/workflow/assistant_tools/ado/test_workflow_with_assistant_with_ado_test_plan_tools.py:test_workflow_with_assistant_with_ado_test_plan_tools",
                    "testCaseHash": -800162226,
                    "patternTemplates": [],
                    "path": "2884"
                },
                {
                    "id": 3105,
                    "uuid": "df7e2a49-ed1c-458e-aac0-5dfaab1e2943",
                    "name": "codemie_test_harness/tests/workflow/direct_tools_calling/test_workflow_with_data_management_tools.py::test_workflow_with_sql_tools_with_hardcoded_args[DataBaseDialect.MS_SQL]",
                    "codeRef": "codemie_test_harness/tests/workflow/direct_tools_calling/test_workflow_with_data_management_tools.py:test_workflow_with_sql_tools_with_hardcoded_args",
                    "parameters": [
                        {
                            "key": "prompt",
                            "value": "{'sql_query': \"SELECT table_name\\n                            FROM\\n                            information_schema.tables\\n                            WHERE\\n                            table_type = 'BASE TABLE'\\n                            AND\\n                            table_catalog = 'autotests'\\n                            AND\\n                            table_schema = 'dbo';\\n                            \"}"
                        },
                        {
                            "key": "toolkit",
                            "value": "Data Management"
                        },
                        {
                            "key": "db_dialect",
                            "value": "mssql"
                        },
                        {
                            "key": "expected_response",
                            "value": "[{'table_name': 'Users'}, {'table_name': 'Products'}]"
                        },
                        {
                            "key": "tool_name",
                            "value": "sql"
                        }
                    ],
                    "attributes": [
                        {
                            "key": "skipif",
                            "value": "False"
                        },
                        {
                            "key": "",
                            "value": "regression"
                        }
                    ],
                    "type": "STEP",
                    "startTime": "2025-09-08T08:57:10.737Z",
                    "endTime": "2025-09-08T08:57:32.809Z",
                    "status": "FAILED",
                    "statistics": {
                        "executions": {
                            "total": 1,
                            "failed": 1
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 1,
                                "ti001": 1
                            }
                        }
                    },
                    "pathNames": {
                        "launchPathName": {
                            "name": "Pytest Regression",
                            "number": 2
                        }
                    },
                    "issue": {
                        "issueType": "ti001",
                        "autoAnalyzed": false,
                        "ignoreAnalyzer": false,
                        "externalSystemIssues": []
                    },
                    "hasChildren": false,
                    "hasStats": true,
                    "launchId": 23,
                    "uniqueId": "auto:7d6e822c868f455cc026c303af84a8ce",
                    "testCaseId": "codemie_test_harness/tests/workflow/direct_tools_calling/test_workflow_with_data_management_tools.py:test_workflow_with_sql_tools_with_hardcoded_args[Data Management,[{'table_name': 'Users'}, {'table_name': 'Products'}],mssql,sql,{'sql_query': \"SELECT table_name\\n                            FROM\\n                            information_schema.tables\\n                            WHERE\\n                            table_type = 'BASE TABLE'\\n                            AND\\n                            table_catalog = 'autotests'\\n                            AND\\n                            table_schema = 'dbo';\\n                            \"}]",
                    "testCaseHash": 847364112,
                    "patternTemplates": [],
                    "path": "3105"
                },
                {
                    "id": 3133,
                    "uuid": "54788617-b214-4057-9a20-3c4d34ee9432",
                    "name": "codemie_test_harness/tests/workflow/direct_tools_calling/test_workflow_with_data_management_tools.py::test_workflow_with_sql_tools_with_overriding_args[DataBaseDialect.MS_SQL]",
                    "codeRef": "codemie_test_harness/tests/workflow/direct_tools_calling/test_workflow_with_data_management_tools.py:test_workflow_with_sql_tools_with_overriding_args",
                    "parameters": [
                        {
                            "key": "prompt",
                            "value": "{'sql_query': \"SELECT table_name\\n                            FROM\\n                            information_schema.tables\\n                            WHERE\\n                            table_type = 'BASE TABLE'\\n                            AND\\n                            table_catalog = 'autotests'\\n                            AND\\n                            table_schema = 'dbo';\\n                            \"}"
                        },
                        {
                            "key": "toolkit",
                            "value": "Data Management"
                        },
                        {
                            "key": "db_dialect",
                            "value": "mssql"
                        },
                        {
                            "key": "expected_response",
                            "value": "[{'table_name': 'Users'}, {'table_name': 'Products'}]"
                        },
                        {
                            "key": "tool_name",
                            "value": "sql"
                        }
                    ],
                    "attributes": [
                        {
                            "key": "skipif",
                            "value": "False"
                        },
                        {
                            "key": "",
                            "value": "regression"
                        }
                    ],
                    "type": "STEP",
                    "startTime": "2025-09-08T08:57:42.220Z",
                    "endTime": "2025-09-08T08:58:04.877Z",
                    "status": "FAILED",
                    "statistics": {
                        "executions": {
                            "total": 1,
                            "failed": 1
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 1,
                                "ti001": 1
                            }
                        }
                    },
                    "pathNames": {
                        "launchPathName": {
                            "name": "Pytest Regression",
                            "number": 2
                        }
                    },
                    "issue": {
                        "issueType": "ti001",
                        "autoAnalyzed": false,
                        "ignoreAnalyzer": false,
                        "externalSystemIssues": []
                    },
                    "hasChildren": false,
                    "hasStats": true,
                    "launchId": 23,
                    "uniqueId": "auto:4ccd523db59b8f0aae122708ec054430",
                    "testCaseId": "codemie_test_harness/tests/workflow/direct_tools_calling/test_workflow_with_data_management_tools.py:test_workflow_with_sql_tools_with_overriding_args[Data Management,[{'table_name': 'Users'}, {'table_name': 'Products'}],mssql,sql,{'sql_query': \"SELECT table_name\\n                            FROM\\n                            information_schema.tables\\n                            WHERE\\n                            table_type = 'BASE TABLE'\\n                            AND\\n                            table_catalog = 'autotests'\\n                            AND\\n                            table_schema = 'dbo';\\n                            \"}]",
                    "testCaseHash": -266643613,
                    "patternTemplates": [],
                    "path": "3133"
                },
                {
                    "id": 3154,
                    "uuid": "0a2d317f-5e4f-4ac3-a5d0-c0c8368357d0",
                    "name": "codemie_test_harness/tests/workflow/direct_tools_calling/test_workflow_with_data_management_tools.py::test_workflow_with_sql_tools_direct[DataBaseDialect.MS_SQL]",
                    "codeRef": "codemie_test_harness/tests/workflow/direct_tools_calling/test_workflow_with_data_management_tools.py:test_workflow_with_sql_tools_direct",
                    "parameters": [
                        {
                            "key": "prompt",
                            "value": "{'sql_query': \"SELECT table_name\\n                            FROM\\n                            information_schema.tables\\n                            WHERE\\n                            table_type = 'BASE TABLE'\\n                            AND\\n                            table_catalog = 'autotests'\\n                            AND\\n                            table_schema = 'dbo';\\n                            \"}"
                        },
                        {
                            "key": "toolkit",
                            "value": "Data Management"
                        },
                        {
                            "key": "db_dialect",
                            "value": "mssql"
                        },
                        {
                            "key": "expected_response",
                            "value": "[{'table_name': 'Users'}, {'table_name': 'Products'}]"
                        },
                        {
                            "key": "tool_name",
                            "value": "sql"
                        }
                    ],
                    "attributes": [
                        {
                            "key": "skipif",
                            "value": "False"
                        },
                        {
                            "key": "",
                            "value": "regression"
                        }
                    ],
                    "type": "STEP",
                    "startTime": "2025-09-08T08:58:09.114Z",
                    "endTime": "2025-09-08T08:58:29.596Z",
                    "status": "FAILED",
                    "statistics": {
                        "executions": {
                            "total": 1,
                            "failed": 1
                        },
                        "defects": {
                            "to_investigate": {
                                "total": 1,
                                "ti001": 1
                            }
                        }
                    },
                    "pathNames": {
                        "launchPathName": {
                            "name": "Pytest Regression",
                            "number": 2
                        }
                    },
                    "issue": {
                        "issueType": "ti001",
                        "autoAnalyzed": false,
                        "ignoreAnalyzer": false,
                        "externalSystemIssues": []
                    },
                    "hasChildren": false,
                    "hasStats": true,
                    "launchId": 23,
                    "uniqueId": "auto:d28f8ed5670ce281b4e111a58251504d",
                    "testCaseId": "codemie_test_harness/tests/workflow/direct_tools_calling/test_workflow_with_data_management_tools.py:test_workflow_with_sql_tools_direct[Data Management,[{'table_name': 'Users'}, {'table_name': 'Products'}],mssql,sql,{'sql_query': \"SELECT table_name\\n                            FROM\\n                            information_schema.tables\\n                            WHERE\\n                            table_type = 'BASE TABLE'\\n                            AND\\n                            table_catalog = 'autotests'\\n                            AND\\n                            table_schema = 'dbo';\\n                            \"}]",
                    "testCaseHash": 1554145012,
                    "patternTemplates": [],
                    "path": "3154"
                }
            ],
            "page": {
                "number": 1,
                "size": 20,
                "totalElements": 4,
                "totalPages": 1
            }
        },
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_LOGS_FOR_TEST_ITEM,
        {"item_id": "111487", "page_number": 1},
        """
            {
              "content" : [ {
                "id" : 4359887,
                "time" : "2025-10-08T10:02:41.368Z",
                "message" : "Starting new HTTPS connection (1): keycloak.eks-core.aws.main.edp.projects.epam.com:443",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359888,
                "time" : "2025-10-08T10:02:41.647Z",
                "message" : "https://keycloak.eks-core.aws.main.edp.projects.epam.com:443 \"POST /auth/realms/codemie-prod/protocol/openid-connect/token HTTP/1.1\" 200 2500",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359889,
                "time" : "2025-10-08T10:02:41.651Z",
                "message" : "Plugin key: f6455cc5-af78-4420-86a9-965ac6f0425e",
                "level" : "INFO",
                "itemId" : 111487
              }, {
                "id" : 4359890,
                "time" : "2025-10-08T10:02:41.652Z",
                "message" : "Making /v1/settings/project request to https://codemie-preview.lab.epam.com/code-assistant-api<class 'dict'>",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359891,
                "time" : "2025-10-08T10:02:41.652Z",
                "message" : "Request body: {'project_name': 'codemie', 'alias': 'cfs_qlbpwnkmgoqgkcc', 'default': False, 'is_global': False, 'credential_type': <CredentialTypes.PLUGIN: 'Plugin'>, 'credential_values': [{'key': 'url', 'value': 'AUTO_GENERATED'}, {'key': 'plugin_key', 'value': 'f6455cc5-af78-4420-86a9-965ac6f0425e'}], 'setting_type': <IntegrationType.PROJECT: 'project'>}",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359892,
                "time" : "2025-10-08T10:02:41.653Z",
                "message" : "Starting new HTTPS connection (1): codemie-preview.lab.epam.com:443",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359893,
                "time" : "2025-10-08T10:02:42.051Z",
                "message" : "https://codemie-preview.lab.epam.com:443 \"POST /code-assistant-api/v1/settings/project HTTP/1.1\" 200 41",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359894,
                "time" : "2025-10-08T10:02:42.052Z",
                "message" : "Received response with status 200",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359895,
                "time" : "2025-10-08T10:02:42.052Z",
                "message" : "Response datasource_type: <class 'dict'>",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359896,
                "time" : "2025-10-08T10:02:42.060Z",
                "message" : "Successfully processed /v1/settings/project request to <class 'dict'>",
                "level" : "INFO",
                "itemId" : 111487
              }, {
                "id" : 4359897,
                "time" : "2025-10-08T10:02:42.060Z",
                "message" : "Making /v1/settings/project request to https://codemie-preview.lab.epam.com/code-assistant-apityping.List[codemie_sdk.models.integration.Integration]",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359898,
                "time" : "2025-10-08T10:02:42.061Z",
                "message" : "Request params: {'page': 0, 'per_page': 200}",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359899,
                "time" : "2025-10-08T10:02:42.062Z",
                "message" : "Starting new HTTPS connection (1): codemie-preview.lab.epam.com:443",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359900,
                "time" : "2025-10-08T10:02:42.562Z",
                "message" : "https://codemie-preview.lab.epam.com:443 \"GET /code-assistant-api/v1/settings/project?page=0&per_page=200 HTTP/1.1\" 200 93345",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359901,
                "time" : "2025-10-08T10:02:42.573Z",
                "message" : "Received response with status 200",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359902,
                "time" : "2025-10-08T10:02:42.573Z",
                "message" : "Response datasource_type: <class 'dict'>",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359903,
                "time" : "2025-10-08T10:02:42.585Z",
                "message" : "Successfully processed /v1/settings/project request to typing.List[codemie_sdk.models.integration.Integration]",
                "level" : "INFO",
                "itemId" : 111487
              }, {
                "id" : 4359904,
                "time" : "2025-10-08T10:02:42.647Z",
                "message" : "Making /v1/settings/project request to https://codemie-preview.lab.epam.com/code-assistant-apityping.List[codemie_sdk.models.integration.Integration]",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359905,
                "time" : "2025-10-08T10:02:42.647Z",
                "message" : "Request params: {'page': 0, 'per_page': 200}",
                "level" : "DEBUG",
                "itemId" : 111487
              }, {
                "id" : 4359906,
                "time" : "2025-10-08T10:02:42.649Z",
                "message" : "Starting new HTTPS connection (1): codemie-preview.lab.epam.com:443",
                "level" : "DEBUG",
                "itemId" : 111487
              } ],
              "page" : {
                "number" : 1,
                "size" : 20,
                "totalElements" : 246,
                "totalPages" : 13
              }
            }
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_USER_INFORMATION,
        {"username": "anton_yeromin"},
        """
        {
            "uuid": "de49a61f-1100-4de6-be8e-4ed7d62f5f27",
            "active": true,
            "id": 4,
            "userId": "anton_yeromin",
            "email": "anton_yeromin@epam.com",
            "fullName": "Anton Yeromin",
            "accountType": "SAML",
            "userRole": "USER",
            "photoLoaded": true,
            "metadata": {
                "last_login": 1757403246837,
                "synchronizationDate": 1757314564405
            },
            "assignedProjects": {
                "epm-cdme": {
                    "projectId": 4,
                    "projectRole": "PROJECT_MANAGER",
                    "entryType": "INTERNAL"
                },
                "anton_yeromin_personal": {
                    "projectId": 6,
                    "projectRole": "PROJECT_MANAGER",
                    "entryType": "PERSONAL"
                }
            }
        },
        """,
    ),
    (
        Toolkit.REPORT_PORTAL,
        ReportPortalTool.GET_DASHBOARD_DATA,
        {"dashboard_id": "2"},
        """
        {
            "description": "dashboard for testing purposes",
            "owner": "dmytro_adamtsev",
            "id": 2,
            "name": "test-dashboard",
            "widgets": []
        },
        """,
    ),
]
