import pytest

EXCEL_TOOL_TEST_DATA = [
    pytest.param(
        "Analyze the data in test_extended.xlsx. Show text content from *ALL VISIBLE* sheets",
        """
            The analysis of the visible sheets in the file **test_extended.xlsx** yields the following data:
            
            ### First Sheet
            | Column 1 | Column 2 | Column 3 |
            | --- | --- | --- |
            | Cars | Test | 222 |
            | Data | Cats | 111 |
            |  |  | Travellers |
            | Tree | Forest |  |
            | Tree | Forest |  |
            | Tree | Forest |  |
            | Tree | Forest |  |
            | Bykes | Red | 877 |
            
            ### Second Sheet
            | Column 1 | Column 2 | Column 3 | Column 4 |
            | --- | --- | --- | --- |
            | Cars | Test | 222 | Second |
            | Data | Cats | 111 | Second |
            |  |  | Travellers | Second |
            | Tree | Forest |  | Second |
            | Tree | Forest |  | Second |
            | Tree | Forest |  | Second |
            | Tree | Forest |  | Second |
            | Bykes | Red | 877 | Second |
            
            The hidden sheet data has been excluded based on the request for visible sheets only. If you need further analysis on specific data or another request, feel free to ask!
        """,
        id="visible_sheets_only",
    ),
    pytest.param(
        "Extract all data from test_extended.xlsx including hidden sheets",
        """
            Here is the extracted data from the `test_extended.xlsx` file, including data from hidden sheets:

            ### First Sheet
            | Column 1 | Column 2 | Column 3 |
            | --- | --- | --- |
            | Cars | Test | 222 |
            | Data | Cats | 111 |
            |  |  | Travellers |
            |  |  |  |
            | Tree | Forest |  |
            | Tree | Forest |  |
            | Tree | Forest |  |
            | Tree | Forest |  |
            |  |  |  |
            | Bykes | Red | 877 |

            ### Second Sheet
            | Column 1 | Column 2 | Column 3 | Column 4 |
            | --- | --- | --- | --- |
            | Cars | Test | 222 | Second |
            | Data | Cats | 111 | Second |
            |  |  | Travellers | Second |
            |  |  |  |  |
            | Tree | Forest |  | Second |
            | Tree | Forest |  | Second |
            | Tree | Forest |  | Second |
            | Tree | Forest |  | Second |
            |  |  |  |  |
            | Bykes | Red | 877 | Second |

            ### Hidden Sheet
            | Column 1 | Column 2 | Column 3 | Column 4 |
            | --- | --- | --- | --- |
            | Cars | Test | 222 | Hidden |
            | Data | Cats | 111 | Hidden |
            |  |  | Travellers | Hidden |
            |  |  |  |  |
            | Tree | Forest |  | Hidden |
            | Tree | Forest |  | Hidden |
            | Tree | Forest |  | Hidden |
            | Tree | Forest |  | Hidden |
            |  |  |  |  |
            | Bykes | Red | 877 | Hidden |
        """,
        id="all_sheets_including_hidden",
    ),
    pytest.param(
        "List all sheet names in test_extended.xlsx",
        """
            The Excel file `test_extended.xlsx` contains the following sheets:

            - First sheet
            - Second sheet
            - Hidden sheet
        """,
        id="all_sheet_names",
    ),
    pytest.param(
        "Get only visible sheet names from test_extended.xlsx",
        """
            The visible sheets in the `test_extended.xlsx` file are:

            - First sheet
            - Second sheet
        """,
        id="visible_sheet_names_only",
    ),
    pytest.param(
        "Get comprehensive statistics about test_extended.xlsx file structure",
        """
            The Excel file `test_extended.xlsx` contains the following structure:

            - **Total Sheets:** 3

            ### Sheet: First sheet
            - **Columns:**
              - Column 1: string, Sample Values: `Cars`, `Data`, ``, ...
              - Column 2: string, Sample Values: `Test`, `Cats`, ``, ...
              - Column 3: string, Sample Values: `222`, `111`, `Travellers`, ...

            ### Sheet: Second sheet
            - **Columns:**
              - Column 1: string, Sample Values: `Cars`, `Data`, ``, ...
              - Column 2: string, Sample Values: `Test`, `Cats`, ``, ...
              - Column 3: string, Sample Values: `222`, `111`, `Travellers`, ...
              - Column 4: string, Sample Values: `Second`

            ### Sheet: Hidden sheet
            - **Columns:**
              - Column 1: string, Sample Values: `Cars`, `Data`, ``, ...
              - Column 2: string, Sample Values: `Test`, `Cats`, ``, ...
              - Column 3: string, Sample Values: `222`, `111`, `Travellers`, ...
              - Column 4: string, Sample Values: `Hidden`

            This summary provides an overview of the column names, data types, and sample values for each sheet within the Excel file.
        """,
        id="file_statistics",
    ),
    pytest.param(
        "Extract data from the first sheet only (index 0) using sheet index from test_extended.xlsx",
        """
            Here is the extracted data from the first sheet of the file `test_extended.xlsx`:

            | Column 1 | Column 2 | Column 3   |
            |:---------|:---------|:-----------|
            | Cars     | Test     | 222        |
            | Data     | Cats     | 111        |
            |          |          | Travellers |
            | Tree     | Forest   |            |
            | Tree     | Forest   |            |
            | Tree     | Forest   |            |
            | Tree     | Forest   |            |
            | Bykes    | Red      | 877        |
        """,
        id="single_sheet_by_index",
    ),
    pytest.param(
        "Extract data only from 'Second sheet' in test_extended.xlsx",
        """
            The data extracted from the "Second sheet" in `test_extended.xlsx` is as follows:

            | Column 1 | Column 2 | Column 3   | Column 4 |
            |----------|----------|------------|----------|
            | Cars     | Test     | 222        | Second   |
            | Data     | Cats     | 111        | Second   |
            |          |          | Travellers | Second   |
            | Tree     | Forest   |            | Second   |
            | Tree     | Forest   |            | Second   |
            | Tree     | Forest   |            | Second   |
            | Tree     | Forest   |            | Second   |
            | Bykes    | Red      | 877        | Second   |
        """,
        id="single_sheet_by_name",
    ),
    pytest.param(
        "Process test_extended.xlsx with data cleaning to remove empty rows and columns on all sheets including hidden",
        """
            The file `test_extended.xlsx` was processed with data cleaning to remove empty rows and columns. Here is a representation of the cleaned Excel sheets:

            ### First Sheet
            | Column 1 | Column 2 | Column 3 |
            |----------|----------|----------|
            | Cars     | Test     | 222      |
            | Data     | Cats     | 111      |
            |          |          | Travellers|
            | Tree     | Forest   |          |
            | Tree     | Forest   |          |
            | Tree     | Forest   |          |
            | Tree     | Forest   |          |
            | Bykes    | Red      | 877      |

            ### Second Sheet
            | Column 1 | Column 2 | Column 3 | Column 4 |
            |----------|----------|----------|----------|
            | Cars     | Test     | 222      | Second   |
            | Data     | Cats     | 111      | Second   |
            |          |          | Travellers| Second   |
            | Tree     | Forest   |          | Second   |
            | Tree     | Forest   |          | Second   |
            | Tree     | Forest   |          | Second   |
            | Tree     | Forest   |          | Second   |
            | Bykes    | Red      | 877      | Second   |

            ### Hidden Sheet
            | Column 1 | Column 2 | Column 3 | Column 4 |
            |----------|----------|----------|----------|
            | Cars     | Test     | 222      | Hidden   |
            | Data     | Cats     | 111      | Hidden   |
            |          |          | Travellers| Hidden   |
            | Tree     | Forest   |          | Hidden   |
            | Tree     | Forest   |          | Hidden   |
            | Tree     | Forest   |          | Hidden   |
            | Tree     | Forest   |          | Hidden   |
            | Bykes    | Red      | 877      | Hidden   |

            The visible sheets have been cleaned, taking away rows and columns that were completely empty. Hidden sheets have been processed but are not visible by default.
        """,
        id="data_cleaning",
    ),
    pytest.param(
        "Analyze test_extended.xlsx with visible_only=False to include hidden sheets",
        """
            The Excel file `test_extended.xlsx` contains three sheets, including a hidden one. Here's a summary of each sheet's content:

            ### First Sheet
            | Column 1 | Column 2 | Column 3 |
            | --- | --- | --- |
            | Cars | Test | 222 |
            | Data | Cats | 111 |
            |   |   | Travellers |
            |   |   |   |
            | Tree | Forest |   |
            | Tree | Forest |   |
            | Tree | Forest |   |
            | Tree | Forest |   |
            |   |   |   |
            | Bykes | Red | 877 |

            ### Second Sheet
            | Column 1 | Column 2 | Column 3 | Column 4 |
            | --- | --- | --- | --- |
            | Cars | Test | 222 | Second |
            | Data | Cats | 111 | Second |
            |   |   | Travellers | Second |
            |   |   |   |   |
            | Tree | Forest |   | Second |
            | Tree | Forest |   | Second |
            | Tree | Forest |   | Second |
            | Tree | Forest |   | Second |
            |   |   |   |   |
            | Bykes | Red | 877 | Second |

            ### Hidden Sheet
            | Column 1 | Column 2 | Column 3 | Column 4 |
            | --- | --- | --- | --- |
            | Cars | Test | 222 | Hidden |
            | Data | Cats | 111 | Hidden |
            |   |   | Travellers | Hidden |
            |   |   |   |   |
            | Tree | Forest |   | Hidden |
            | Tree | Forest |   | Hidden |
            | Tree | Forest |   | Hidden |
            | Tree | Forest |   | Hidden |
            |   |   |   |   |
            | Bykes | Red | 877 | Hidden |

            ### Observations:
            - Each sheet has a similar structure, with `Column 1` and `Column 2` containing repeated entries.
            - The hidden sheet appears to be similar to the second sheet but with the label 'Hidden' in `Column 4`.
            - The first sheet doesn't have a `Column 4` like the other two sheets.
            - There are several rows with missing values, especially in `Column 1` and `Column 2`.

            Let me know if you need more in-depth analysis or specific insights from these sheets!
        """,
        id="hidden_sheet_visibility",
    ),
    pytest.param(
        "Analyze column structure and data types in test_extended.xlsx",
        """
            The Excel file `test_extended.xlsx` contains a total of 3 sheets: "First sheet", "Second sheet", and a "Hidden sheet". Here's an overview of the column structure and data types for each sheet:

            ### Sheet: First sheet
            - **Columns:**
              - **Column 1**: string (Sample Values: `Cars`, `Data`, ...)
              - **Column 2**: string (Sample Values: `Test`, `Cats`, ...)
              - **Column 3**: string (Sample Values: `222`, `111`, `Travellers`, ...)

            ### Sheet: Second sheet
            - **Columns:**
              - **Column 1**: string (Sample Values: `Cars`, `Data`, ...)
              - **Column 2**: string (Sample Values: `Test`, `Cats`, ...)
              - **Column 3**: string (Sample Values: `222`, `111`, `Travellers`, ...)
              - **Column 4**: string (Sample Value: `Second`)

            ### Sheet: Hidden sheet
            - **Columns:**
              - **Column 1**: string (Sample Values: `Cars`, `Data`, ...)
              - **Column 2**: string (Sample Values: `Test`, `Cats`, ...)
              - **Column 3**: string (Sample Values: `222`, `111`, `Travellers`, ...)
              - **Column 4**: string (Sample Value: `Hidden`)

            All columns across the sheets predominantly contain string data types. If you have any further questions or need additional analysis, feel free to ask!
        """,
        id="column_structure_analysis",
    ),
    pytest.param(
        "Normalize test_extended.xlsx data to standard tabular structure with markdown format",
        """
            Here is the normalized content from the `test_extended.xlsx`, structured in markdown tables:

            ### First Sheet
            ```markdown
            | Column 1 | Column 2 | Column 3 |
            |----------|----------|----------|
            | Cars     | Test     | 222      |
            | Data     | Cats     | 111      |
            |          |          | Travellers|
            | Tree     | Forest   |          |
            | Tree     | Forest   |          |
            | Tree     | Forest   |          |
            | Tree     | Forest   |          |
            | Bykes    | Red      | 877      |
            ```

            ### Second Sheet
            ```markdown
            | Column 1 | Column 2 | Column 3 | Column 4 |
            |----------|----------|----------|----------|
            | Cars     | Test     | 222      | Second   |
            | Data     | Cats     | 111      | Second   |
            |          |          | Travellers| Second  |
            | Tree     | Forest   |          | Second   |
            | Tree     | Forest   |          | Second   |
            | Tree     | Forest   |          | Second   |
            | Tree     | Forest   |          | Second   |
            | Bykes    | Red      | 877      | Second   |
            ```

            ### Hidden Sheet
            ```markdown
            | Column 1 | Column 2 | Column 3 | Column 4 |
            |----------|----------|----------|----------|
            | Cars     | Test     | 222      | Hidden   |
            | Data     | Cats     | 111      | Hidden   |
            |          |          | Travellers| Hidden  |
            | Tree     | Forest   |          | Hidden   |
            | Tree     | Forest   |          | Hidden   |
            | Tree     | Forest   |          | Hidden   |
            | Tree     | Forest   |          | Hidden   |
            | Bykes    | Red      | 877      | Hidden   |
            ```

            Each sheet has been normalized into a standard tabular markdown format.
        """,
        id="tabular_normalization",
    ),
    pytest.param(
        "Perform comprehensive analysis of all sheets in test_extended.xlsx including data summary",
        """
            The file `test_extended.xlsx` contains the following information:

            ### Overall Summary
            - **Total Sheets:** 3

            ### Detailed Sheet Information

            #### 1. First Sheet
            - **Columns:**
              | Column Name | Data Type | Sample Values     |
              |-------------|-----------|-------------------|
              | Column 1    | string    | `Cars`, `Data`, ...|
              | Column 2    | string    | `Test`, `Cats`, ...|
              | Column 3    | string    | `222`, `111`, ...  |

            #### 2. Second Sheet
            - **Columns:**
              | Column Name | Data Type | Sample Values     |
              |-------------|-----------|-------------------|
              | Column 1    | string    | `Cars`, `Data`, ...|
              | Column 2    | string    | `Test`, `Cats`, ...|
              | Column 3    | string    | `222`, `111`, ...  |
              | Column 4    | string    | `Second`           |

            #### 3. Hidden Sheet
            - **Columns:**
              | Column Name | Data Type | Sample Values     |
              |-------------|-----------|-------------------|
              | Column 1    | string    | `Cars`, `Data`, ...|
              | Column 2    | string    | `Test`, `Cats`, ...|
              | Column 3    | string    | `222`, `111`, ...  |
              | Column 4    | string    | `Hidden`           |

            These sheets include a variety of string data across the columns with consistent format among the visible and hidden sheets.
        """,
        id="comprehensive_analysis",
    ),
]

DOCX_TOOL_TEST_DATA = [
    pytest.param(
        "Extract plain text from test_extended.docx and show it",
        """
            Here is the extracted plain text from the document `test_extended.docx`:

            ---

            1. **Getting Started with AI/RunTM CodeMie**

               This section provides a brief description of what AI/RunTM CodeMie is and describes how to start using the AI/RunTM CodeMie tool as soon as possible.

               **1.1 What is AI/RunTM CodeMie?**

               AI/RunTM CodeMie is a sophisticated AI assistant tool tailored specifically for developers. AI/RunTM CodeMie is an innovative LLM-powered platform designed to help users address specific challenges and find solutions for their needs. Unlike conventional large language models (LLMs) such as ChatGPT, Bard, and Copilot, AI/RunTM CodeMie is engineered to support development processes more comprehensively. It integrates seamlessly with essential development tools including Git, Jira, Confluence, and various search engines. This integration empowers AI/RunTM CodeMie to go beyond the capabilities of a standard chatbot, enabling it to manage Jira issues, devise appropriate implementations, and generate pull requests.

               AI/RunTM CodeMie leverages AI to automate coding tasks, reduce technical debt, streamline code reviews and legacy application migrations, enhance onboarding, improve information access and analysis, optimize call center operations, ensure consistent customer support, maintain data security, and analyze market sentiment, ultimately enhancing productivity and reducing costs. The development of such a powerful assistant necessitates extensive customization and fine-tuning. The following sections will delve into the intricate adjustments and configurations required to harness the full potential of AI/RunTM CodeMie.

               **1.2 What Are AI/RunTM CodeMie Capabilities?**

               AI/RunTM CodeMie efficiently addresses numerous tasks across varying difficulty levels. Below is an overview of AI/RunTM CodeMie’s key capabilities:

               - **Comprehensive SDLC Smart Assistance and Assistants Library:** AI/RunTM CodeMie offers robust smart assistance across all phases of the SDLC process by leveraging a variety of AI assistant roles, such as Business Analyst (BA), Developer, Quality Assurance (QA), Project Manager (PM), and more. These pre-built AI assistants enhance performance and productivity, automate routine work, significantly reducing process costs and accelerating the software development cycle. The platform comes with a comprehensive library of pre-built AI assistants tailored to various roles within the SDLC to suit the diverse needs within a project.

              - **Assistants Constructor:** Provides the flexibility to create personalized assistants equipped with specific tools and abilities tailored to your project's needs.

              - **Indexing and Data Management:** AI/RunTM CodeMie provides options for data indexing, including the ability to monitor the current progress and status of the indexing process, perform incremental or full reindexing, and manage indexed data sources effectively. Supported data sources include Jira, Confluence, various file formats (PDF, PPT, Excel, etc.), and Git.

              - **Support for Multi-Agent Workflows:** AI/RunTM аCodeMie supports multi-agent workflows, allowing multiple AI assistants to collaborate seamlessly on complex tasks and workflows. This capability covers use cases where different agents need to interact and share information to achieve a common goal, enhancing coordination and efficiency across various phases of the SDLC.

              - **Ease of Use for Beginners:** Simple use cases for newcomers include code review, newcomer training, and user story creation. These require minimal setup, such as configuring your Git token for code-related tasks or your Jira token for project management tasks.

              - **Extensive Library of Tools:** AI/RunTM CodeMie includes a wide array of tools to support various aspects of software development and project management:
                - **Version Control Systems (VCS):** Tools for managing and tracking changes in the codebase, such as Git.
                - **Codebase Tools:** Tools for code review, static code analysis, and automated code formatting.
                - **Research Tools:** Tools to assist in gathering and organizing research data and documentation.
                - **Cloud Tools:** Integration with major cloud providers for deployment, monitoring, and management of cloud resources.
                - **Project Management Tool (Jira:** For project management, task tracking, and issue tracking, **Confluence:** For documentation, knowledge sharing, and collaboration.)
                - **Open API:** Integration with various open APIs to extend functionality and connect with other services.
                - **Notification Tools:** Tools for sending notifications and alerts via email, chat, or other communication channels.
                - **Data Management Tools:** Tools for querying Elasticsearch indexes.
                - **Git Access Management:** Keycloak
                - **Plugin Open API Notification File Management Data Management Quality Assurance**

              There is no priority or sequential system in place. Everything depends on the given instructions. It is possible to instruct the model to use a specific data source for a particular use case or provide a description for the data source when it is created. Data source descriptions are provided to the model so it can understand better use cases for it.

              (The text continues with further details that describe how to utilize specific features and integration steps for various contexts and platforms including Keycloak, SonarQube, SQL, Telegram, Azure, and much more.)

            ---

            Above is a portion of the extracted text. It seems this document provides an in-depth introduction and guide to using AI/RunTM CodeMie, a tool for developers, detailing its capabilities, tools, integrations, and operational instructions. Let me know if you need more specific details or further assistance!
        """,
        id="text",
    ),
    pytest.param(
        "Extract text with metadata from test_extended.docx and show it",
        """
            ### Extracted Text with Metadata from *test_extended.docx*

            **Metadata:**
            - **Title:** *Not Specified*
            - **Author:** *Not Specified*
            - **Created Date:** 2025-09-26T09:33:00+00:00
            - **Modified Date:** 2025-09-26T09:36:00+00:00
            - **Keywords:** *Not Specified*
            - **Subject:** *Not Specified*
            - **Category:** *Not Specified*
            - **Paragraph Count:** 835
            - **Table Count:** 2
            - **Section Count:** 1
            - **Word Count:** 7,434

            **Extracted Text Snippet:**
            The document primarily includes sections about AI/Run™ CodeMie, describing its capabilities, features, and integrations, as well as detailed guides for setup and utilization. Below is a brief example of the content:

            ---
            #### Chapter Excerpts:
            **1. Getting Started with AI/Run™ CodeMie**
            - Introduction to AI/Run™ CodeMie and its functionalities.
            - Highlights include automating coding tasks, reducing technical debt, optimizing customer support, and managing tools like Git, Jira, and Confluence.

            **1.2 What Are AI/Run™ CodeMie Capabilities?**
            - Comprehensive SDLC Smart Assistance and Assistants Library.
            - Tools for various applications such as version control systems, cloud integration, and multi-agent workflows.

            **2.9 Tool Integration Overview**
            - Detailed steps to integrate Keycloak, SonarQube, SQL databases, Telegram, Azure, GCP, AWS, Kubernetes, and more.

            **3. How to Work With Assistants**
            - Insights into creating assistants, using templates, and customization options like workflows, tools, and specific roles.

            ---

            If you need specific sections, tables, or a detailed breakdown, let me know!
        """,
        id="text_with_metadata",
    ),
    pytest.param(
        "Extract document structure from test_extended.docx",
        """
            ### Document Structure for *test_extended.docx*

            #### Main Sections and Subsections:

            1. **Getting Started with AI/RunTM CodeMie**
               - **1.1 What is AI/RunTM CodeMie?**
               - **1.2 What Are AI/RunTM CodeMie Capabilities?**
               - **1.3 Meet the AI/Run FAQ Assistant**
               - **1.4 Help center**

            2. **Tools and Integrations Overview**
               - **2.9 Tool Integration Overview**
                 - *2.9.1 Keycloak*
                 - *2.9.2 SonarQube*
                 - *2.9.5 SQL*
                 - *2.9.6 Telegram*
                 - *2.9.7 Azure*
                 - *2.9.8 GCP*
                 - *2.9.9 AWS*
                 - *2.9.10 Kubernetes*
                 - *2.9.11 Webhook*
                 - *2.9.12 HTML Preview*
                 - *2.9.13 Elastic*

            3. **MCP Overview**
               - **2.11 Adding an MCP Server**
               - **2.11 Using MCP Tools in Assistants**

            4. **Data Sources and Assistant Tools**
               - **2.12 What is the difference between a Data Source and an Assistant Tool in CodeMie?**
               - **2.12 Administrative tools overview**
               - **2.13 Processing Pictures**

            5. **How to Work With Assistants**
               - **3.1 Assistant Templates**
               - **3.2 Create Assistant From a Template**
               - **3.9 Restore System Instructions**

            ---

            Let me know if you'd like further details extracted from specific sections or explored further!
        """,
        id="structure_only",
    ),
    pytest.param(
        "Extract tables from test_extended.docx",
        """
            ### Extracted Tables from *test_extended.docx*

            #### Table 1: Tools and Integrations Overview
            | **Tools Name**                          | **Integration Required** | **Integration Name** |
            |----------------------------------------|--------------------------|-----------------------|
            | Project Management => Jira             | Yes                      | Jira                 |
            | Git (with operations)                  | Yes                      | Git                  |
            | Project Management => Confluence       | Yes                      | Confluence           |
            | Cloud => Kubernetes                    | Yes                      | Kubernetes           |
            | Cloud => AWS                           | Yes                      | AWS                  |
            | Cloud => GCP                           | Yes                      | GCP                  |
            | Access Management => Keycloak          | Yes                      | Keycloak             |
            | Cloud => Azure                         | Yes                      | Azure                |
            | Cloud => AzureDevOps                   | Yes                      | AzureDevOps          |
            | Data Management => SQL                 | Yes                      | SQL                  |
            | Notification => Email                  | Yes                      | Email                |
            | Codebase Tools => Sonar                | Yes                      | Sonar                |
            | Research => Google Searches, Places    | No                       | ----                 |
            | Quality Assurance => ZephyrCloud, Squad| Yes                      | ZephyrCloud, Squad   |

            > **Note**: This table lists numerous tools and integrations required, along with operations (e.g., Git, Jira, Kubernetes). Additional details (e.g., various Git operations such as branch creation, pull requests) are included in raw text.

            ---

            #### Table 2: Assistant Overview
            | **Name**                            | **Description/Integrated Tools**                                                                                                                | **Assistant’s Tools**                                                                      |
            |-------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
            | Epic/User Story Compose             | Analyzes and generates requirements for the project. Note: Uses deprecated Jira tool.                                                           | Jira Issue Management                                                                     |
            | Release Manager Assistant           | Supports release processes, generates notes, closes tickets.                                                                                    | Git, VCS (GitLab), Jira                                                                   |
            | Junior Python Langchain Developer   | Develops tools within Langchain framework.                                                                                                      | Git, Jira                                                                                 |
            | Junior JavaScript Vue Developer     | Develops high-quality, responsive web applications using Vue.js.                                                                                 | Git, Jira                                                                                 |
            | Design to Code Developer            | Translates designs into responsive web apps, optimizes performance.                                                                              | VCS (GitLab), File Management                                                             |
            | QA Checklist Assistant              | Generates QA checklists.                                                                                                                        | Jira, Confluence                                                                          |
            | QA Test Case Assistant              | Generates test cases based on specifications.                                                                                                   | Jira, Confluence                                                                          |
            | Code Reviewer                       | Reviews Git pull requests and creates comments.                                                                                                 | Git Tools                                                                                |
            | Cloud Assistant                     | Prebuilt assistant to help with cloud system interactions.                                                                                      | Cloud Tools (Kubernetes, AWS, GCP, Azure)                                                |
            | ChatGPT                             | Acts as a simple chatbot.                                                                                                                       | None                                                                                      |
            | CSV Analyst                         | Analyzes CSV files.                                                                                                                             | None                                                                                      |

            > **Note**: This table outlines assistant types, their roles, and tools integrated. Additional assistants (e.g., CodeMie, Cloud) appear in subsequent rows.

            ---

            If you need further details or specific tables expanded, let me know!
        """,
        id="table_extraction",
    ),
    pytest.param(
        "Generate summary for test_extended.docx",
        """
            ### Summary of *test_extended.docx*

            The document serves as a comprehensive guide to **AI/Run™ CodeMie**, an advanced AI assistant platform aimed at optimizing software development processes. It details the platform's diverse capabilities, including:

            - **SDLC Assistance**: Smart tools for every phase of the Software Development Life Cycle.
            - **Tool Integrations**: Seamless integration with platforms like Git, Jira, Confluence, AWS, GCP, Kubernetes, and SonarQube.
            - **Data Indexing**: Simplifying data access and management.
            - **Multi-Agent Workflows**: Facilitating efficient team collaboration.

            Key topics include:

            1. **Administrative Tools**:
               - Overview of management features and functionalities.
               - Processes for onboarding and creating assistants using templates or custom configurations.

            2. **Integrations**:
               - Detailed integration steps for platforms like AWS, Kubernetes, SQL databases, and more.

            3. **Features**:
               - MCP server integration.
               - Automated workflows (e.g., CRON scheduling).
               - Email notifications and FAQ support.

            The document emphasizes enhancing productivity, collaboration, and streamlining development workflows for developers and teams.

            Let me know if you need further details or additional analysis!
        """,
        id="summary",
    ),
    pytest.param(
        "Extract plain text from test_extended.docx then analyze it's sentiment to determine whether the overall tone is positive, neutral, or negative.",
        """
            ### Sentiment Analysis of *test_extended.docx*

            #### **Sentiment**: Positive
            The text reflects a positive tone, emphasizing the platform's benefits, extensive integrations, and potential to enhance productivity and efficiency in software development. The language conveys enthusiasm and confidence in AI/Run™ CodeMie's role in streamlining workflows.

            #### **Language**: English
            The document is written entirely in English.

            #### **Readability Score**: 6.0
            This indicates that the document is relatively easy to read and accessible to a wide audience, likely targeting professionals familiar with software development concepts.

            #### **Pages Analyzed**: All
            The sentiment analysis covered the entire document for a comprehensive understanding.

            If you need further breakdowns or alternative types of analysis, let me know!
        """,
        id="analyze",
    ),
    pytest.param(
        "Extracty text from specific pages '1-3' from test_extended.docx and show it",
        """
            ### Extracted Plain Text from Pages 1–3 of *test_extended.docx*

            #### **1. Getting Started with AI/Run™ CodeMie**
            This section introduces AI/Run™ CodeMie, detailing its purpose and how to immediately start using the platform.

            **1.1 What Is AI/Run™ CodeMie?**
            AI/Run™ CodeMie is an AI assistant tailored for developers, providing solutions for software challenges and integrating with tools like Git, Jira, Confluence, and search engines. Unlike traditional AI models (e.g., ChatGPT, Bard, Copilot), AI/Run™ CodeMie goes beyond basic chatbot functionalities by automating tasks, managing Jira issues, generating pull requests, reducing technical debt, and enhancing data security and productivity.

            **1.2 What Are AI/Run™ CodeMie’s Capabilities?**
            Highlights include:
            - **SDLC Assistance**: Pre-built assistants tailored for roles such as Business Analyst, QA, Developer, and Project Manager.
            - **Assistants Constructor**: Build customized AI assistants with specific tools for project needs.
            - **Data Indexing**: Supports incremental data indexing from Jira, Confluence, Git, and various file formats.
            - **Multi-Agent Workflows**: Enables collaboration among AI assistants for complex tasks.

            Tools included: version control, code review, cloud deployments, project management (e.g., Jira, Confluence), notifications, and data management tools like Elasticsearch.

            **1.3 Meet the AI/Run FAQ Assistant**
            To start using AI/Run™ CodeMie:
            - Log in via SSO.
            - Access the FAQ assistant to start conversations and explore onboarding features.

            **1.4 Help Center**
            The Help Center provides resources for assistance, learning, and updates, including:
            - AI Assistants for FAQ, feedback, and real-time support.
            - User guides and video tutorials.
            - Tracking product updates.

            ---

            #### **2.9 Tool Integration Overview**
            This section explains how to integrate tools with AI/Run™ CodeMie, using **Keycloak** as an example.

            **Keycloak Integration Steps**:
            1. Select the realm in Keycloak.
            2. Create or use an existing client (e.g., admin-cli).
            3. Configure service account roles.
            4. Copy the client secret from credentials.
            5. Configure Keycloak settings in AI/Run™ CodeMie:
               - Base URLpatch_langchain_google_vertexai()
               - Realm
               - Client ID
               - Client Secret

            Assistants can then be created with access to Keycloak for specific projects, enabling enhanced system integrations.

            ---

            Let me know if you need further processing for other pages or specific sections within this extracted content!
        """,
        id="text_pages_1_3",
    ),
    pytest.param(
        "Extract text from specific pages '1,5,10' from test_extended.docx and show it",
        """
            ### Extracted Text from Specific Pages (1, 5, 10) of *test_extended.docx*

            ---

            ### **Page 1: Introduction to AI/Run™ CodeMie**
            #### **1. Getting Started with AI/Run™ CodeMie**
            This section introduces AI/Run™ CodeMie, detailing how to get started quickly.

            **1.1 What is AI/Run™ CodeMie?**
            AI/Run™ CodeMie is an AI-driven assistant designed for developers, integrating key tools like Git, Jira, Confluence, etc., to address challenges effectively. It goes beyond standard use-cases seen in tools like ChatGPT or Copilot, allowing:
            - Jira issue tracking.
            - Pull request generation and implementation recommendations.
            - Legacy migration and technical debt reduction.
            - Enhanced onboarding and productivity optimization.

            AI/Run™ CodeMie offers automation on coding tasks, system integrations, and improved customer support, among other features.

            **1.2 Capabilities of AI/Run™ CodeMie**
            Key highlights include:
            - **Comprehensive SDLC Assistance**: Pre-built assistants like QA analysts, developers, PMs, etc.
            - **Assistants Constructor**: Build custom assistants as per project requirements.
            - **Data Indexing**: Manage incremental or full indexing from Jira, Confluence, Git repositories, and other formats.
            - **Multi-Agent Workflows**: Support for collaborative tasks among multiple AI agents.
            - **Extensive Tool Library**: Includes tools for cloud deployment, project management, quality assurance, and notifications.

            **1.3 Meet the FAQ Assistant**
            Provides onboarding solutions and covers general queries, helping users adapt to the platform faster.

            ---

            ### **Page 5: Integration Examples**
            #### **2.9.5 SQL Database**
            AI/Run™ CodeMie integrates seamlessly with SQL databases (e.g., PostgreSQL or MySQL).
            **Steps to Integrate SQL:**
            1. Navigate to the “Integrations” tab.
            2. Provide necessary credentials (e.g., database name, username, password).
            3. Modify or create an assistant with SQL access to perform table operations or database queries.

            #### **2.9.6 Telegram Messenger**
            Since version 0.12.0, AI/Run assistants can now operate with Telegram for bot manipulation and real-time chat interactions:
            **Steps to Set Up Telegram Bot Integration**:
            1. Create a bot through Telegram’s BotFather.
            2. Generate a bot token and apply it during integration setup within AI/Run™ CodeMie.
            3. Add Telegram as a project-level integration for assistants.

            ---

            ### **Page 10: Advanced Integrations**
            #### **Webhook Integration**
            AI/Run™ CodeMie assistants support webhook-based triggers, facilitating automation from external systems (e.g., customer support or pull request generation).
            **Key Steps**:
            1. Enable webhook triggers for assistants/workflows/datasources.
            2. Provide required credentials such as Webhook ID and Secure Access Key during integration setup.

            Applications include:
            - Trigger assistant responses as pull requests are created.
            - Notify users through real-time workflows for Jira updates.
            - Automate support assistants for helpdesk ticket creation.

            ---

            Let me know if you need further assistance or more pages analyzed!
        """,
        id="text_pages_1_5_10",
    ),
    pytest.param(
        "Extract images from test_extended.docx",
        """
            ### Extracted Image from *test_extended.docx*

            #### Image 1:
            - **Format**: PNG
            - **Description**: An image depicting **capability configurations**, particularly configurations related to client authentication and authorization flows.
            - **Text Content Associated**:
              ```
              ### Capability config

              **Client authentication**
              - On

              **Authorization**
              - Off

              **Authentication flow**
              - **Standard flow** ✅
              - **Direct access grants** ✅
              - Implicit flow ☐
              - **Service accounts roles** ✅
              - OAuth 2.0 Device Authorization Grant ☐
              - OIDC CIBA Grant ☐
              ```

            The image encompasses these configurations, potentially used for documenting integration setups.

            - **Position**:
              - **Page**: 1
              - **Coordinates**: Top-left corner

            Let me know if you'd like to download the image or process additional queries!
        """,
        id="image_extraction",
    ),
    pytest.param(
        "From test_extended.docx extract and show the text with OCR from images",
        """
            ### Extracted Text with OCR from Images in *test_extended.docx*

            #### **Image 1: Capability Configuration**
            The image contains text related to client authentication, authorization settings, and available flows. Below is the OCR-extracted text:

            ```
            **Capability config**

            - **Client authentication**
              - 🟦 On

            - **Authorization**
              - ⚪ Off

            - **Authentication flow**
              - ☑️ Standard flow
              - ☑️ Direct access grants
              - ☐ Implicit flow
              - ☑️ Service accounts roles
              - ☐ OAuth 2.0 Device Authorization Grant
              - ☐ OIDC CIBA Grant
            ```

            This image primarily highlights authentication configurations, flow types, and the enabling/disabling of various features.

            ---

            Let me know if you'd like to perform further analysis or extract more details!
        """,
        id="text_with_images",
    ),
]
