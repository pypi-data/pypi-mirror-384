import os
from pathlib import Path
from typing import Optional

from codemie_sdk.models.workflow import (
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
    WorkflowMode,
)

from codemie_test_harness.tests import PROJECT
from codemie_test_harness.tests.utils.base_utils import (
    BaseUtils,
    get_random_name,
    wait_for_entity,
    wait_for_completion,
)
from codemie_test_harness.tests.utils.http_utils import RequestHandler

workflow_endpoint = "/v1/workflows"


class WorkflowUtils(BaseUtils):
    def send_request_to_create_workflow_endpoint(
        self, request: WorkflowCreateRequest
    ) -> dict:
        """
        Send request to workflow creation endpoint without raising error for response status codes.

        Args:
            request: The workflow creation request containing required fields:
                    - name: Name of the workflow
                    - description: Description of the workflow
                    - project: Project identifier
                    - yaml_config: YAML configuration for the workflow
                    Optional fields with defaults:
                    - mode: WorkflowMode (defaults to SEQUENTIAL)
                    - shared: bool (defaults to False)
                    - icon_url: Optional URL for workflow icon

        Returns:
            Raw response from '/v1/workflows' endpoint
        """
        api_domain = os.getenv("CODEMIE_API_DOMAIN")
        verify_ssl = os.getenv("VERIFY_SSL", "").lower() == "true"

        request_handler = RequestHandler(api_domain, self.client.token, verify_ssl)

        return request_handler.post(
            workflow_endpoint, dict, json_data=request.model_dump()
        )

    def send_create_workflow_request(
        self,
        workflow_yaml,
        workflow_type=WorkflowMode.SEQUENTIAL,
        description=None,
        workflow_name=None,
        shared=False,
        project=None,
    ):
        workflow_name = get_random_name() if not workflow_name else workflow_name

        request = WorkflowCreateRequest(
            name=workflow_name,
            description=description if description else "Test Workflow",
            project=project if project else PROJECT,
            mode=workflow_type,
            yaml_config=workflow_yaml,
            shared=shared,
        )

        response = self.client.workflows.create_workflow(request)

        return response, workflow_name

    def create_workflow(
        self,
        workflow_type,
        workflow_yaml,
        description=None,
        workflow_name=None,
        shared=False,
        project_name=None,
    ):
        """
        Sends request to workflow creation endpoint and waits for workflow created.
        """
        response = self.send_create_workflow_request(
            workflow_yaml,
            workflow_type,
            description,
            workflow_name,
            shared,
            project_name,
        )

        return wait_for_entity(
            lambda: self.client.workflows.list(per_page=200),
            entity_name=response[1],
        )

    def execute_workflow(
        self,
        workflow,
        execution_name,
        user_input="",
        file_name: Optional[str] = None,
    ):
        self.client.workflows.run(workflow, user_input=user_input, file_name=file_name)
        executions = self.client.workflows.executions(workflow)
        execution_id = next(
            row.execution_id for row in executions.list() if row.prompt == user_input
        )
        states_service = executions.states(execution_id)
        state = wait_for_entity(
            lambda: states_service.list(),
            entity_name=execution_name,
        )

        wait_for_completion(execution_state_service=states_service, state_id=state.id)
        return states_service.get_output(state_id=state.id).output

    def run_workflow(self, workflow_id, user_input=""):
        return self.client.workflows.run(workflow_id=workflow_id, user_input=user_input)

    def get_workflow(self, workflow_id):
        return self.client.workflows.get(workflow_id)

    def get_workflow_execution(self, test_workflow_id, execution_id):
        return self.client.workflows.executions(test_workflow_id).get(execution_id)

    def get_workflow_executions_states(self, test_workflow_id, execution_id):
        return self.client.workflows.executions(test_workflow_id).states(execution_id)

    def send_update_workflow_request(
        self,
        workflow_id,
        request: WorkflowUpdateRequest,
    ):
        return self.client.workflows.update(workflow_id, request)

    def update_workflow(
        self,
        workflow,
        name=None,
        description=None,
        project=None,
        yaml_config=None,
        mode=None,
        shared=None,
    ):
        name = name if name else workflow.name
        request = WorkflowUpdateRequest(
            name=name,
            project=project if project else workflow.project,
            description=description if description else workflow.description,
            yaml_config=yaml_config if yaml_config else workflow.yaml_config,
            mode=mode if mode else workflow.mode,
            shared=shared if shared else workflow.shared,
        )
        self.send_update_workflow_request(workflow.id, request=request)

        return wait_for_entity(
            lambda: self.client.workflows.list(per_page=200),
            entity_name=name,
        )

    def get_prebuilt_workflows(self):
        return self.client.workflows.get_prebuilt()

    @staticmethod
    def open_workflow_yaml(path, yaml_file, values: dict = None):
        yaml_path = os.path.join(os.path.dirname(__file__), f"../{path}/{yaml_file}")
        assert os.path.exists(yaml_path), f"YAML file not found: {yaml_path}"

        with open(yaml_path, encoding="utf-8") as file:
            template = file.read()

        return template.format(**values) if values else template

    def delete_workflow(self, workflow):
        self.client.workflows.delete(workflow.id)

    def get_executions(self, workflow):
        return self.client.workflows.executions(workflow.id).list()

    def get_first_execution(self, workflow):
        return self.get_executions(workflow)[0]

    def extract_triggered_tools_from_execution(self, workflow, execution=None):
        """
        Extract triggered tools from workflow execution thoughts.

        Args:
            workflow: Workflow object
            execution: Execution object

        Returns:
            list: List of triggered tool names in lowercase
        """

        if execution:
            execution_id = execution.execution_id
        else:
            executions = self.get_executions(workflow)
            assert len(executions) > 0, "No workflow executions found"
            first_execution = executions[0]
            execution_id = first_execution.execution_id

        triggered_tools = []

        # Get execution states to find thought IDs
        states_service = self.client.workflows.executions(workflow.id).states(
            execution_id
        )
        states = states_service.list()

        if not states:
            return triggered_tools

        # Collect all thought IDs from states
        thought_ids = []
        for state in states:
            if hasattr(state, "thoughts") and state.thoughts:
                for thought in state.thoughts:
                    thought_ids.append(thought.id)

        if not thought_ids:
            return triggered_tools

        # Get detailed thoughts information
        executions_service = self.client.workflows.executions(workflow.id)
        thoughts_data = executions_service.get_thoughts(execution_id, thought_ids)

        # Convert thoughts objects to dictionaries for processing
        thoughts_dict_data = [thought.model_dump() for thought in thoughts_data]

        # Extract triggered tools from thoughts
        triggered_tools = self._extract_tools_from_thoughts(thoughts_dict_data)

        return triggered_tools

    def upload_file(self, file_path: Path):
        return self.client.files.bulk_upload([file_path])

    @staticmethod
    def _extract_tools_from_thoughts(thoughts_data):
        """
        Extract tool names from thoughts data recursively.

        Args:
            thoughts_data: List of thought objects with nested children

        Returns:
            list: List of triggered tool names in lowercase
        """
        triggered_tools = []

        def process_thought(_thought):
            # Check if this thought represents a tool call
            author_name = _thought.get("author_name", "")
            author_type = _thought.get("author_type", "")

            # Filter out 'Codemie Thoughts' and non-tool entries
            if (
                author_type == "Tool"
                and author_name
                and author_name != "Codemie Thoughts"
            ):
                triggered_tools.append(author_name.lower())

            # Recursively process children
            children = _thought.get("children", [])
            for child in children:
                process_thought(child)

        # Process all top-level thoughts
        if isinstance(thoughts_data, list):
            for thought in thoughts_data:
                process_thought(thought)

        return triggered_tools
