"""Random values workflow plugin module"""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from http import HTTPStatus
from time import sleep

from cmem.cmempy.api import config, get_json
from cmem.cmempy.workflow.workflow import execute_workflow_io, get_workflows_io
from cmem_plugin_base.dataintegration.context import ExecutionContext, ExecutionReport
from cmem_plugin_base.dataintegration.description import Icon, Plugin, PluginParameter
from cmem_plugin_base.dataintegration.entity import (
    Entities,
    Entity,
    EntityPath,
    EntitySchema,
)
from cmem_plugin_base.dataintegration.plugins import PluginLogger, WorkflowPlugin
from cmem_plugin_base.dataintegration.ports import FixedNumberOfInputs, FlexibleSchemaPort
from cmem_plugin_base.dataintegration.typed_entities.file import FileEntitySchema
from cmem_plugin_base.dataintegration.types import (
    BoolParameterType,
    IntParameterType,
    StringParameterType,
)
from cmem_plugin_base.dataintegration.utils import setup_cmempy_user_access
from requests import HTTPError

from cmem_plugin_loopwf import exceptions
from cmem_plugin_loopwf.workflow_type import SuitableWorkflowParameterType

DOCUMENTATION = """Run another workflow once per incoming entity.

## Overview

- **Per-entity execution**: For every entity on the input port, this task starts one selected
  sub-workflow.
- **Execution modes**: Runs sequentially by default or in parallel with a configurable
  concurrency.
- **Input handover**: Each entity is converted to a JSON object and provided to the sub-workflow
  via its single replaceable (variable) input dataset.
- **Optional pass-through**: Optionally forwards the original input entities to the output port;
  it never returns results produced by the sub-workflow.
- **File support (beta)**: When processing file entities and a `input_mime_type` is set, the file
  content is sent to the sub-workflow instead of the file metadata.

## How It Works

1. Read entities from the single input port (flexible schema).
2. Convert each entity to a flat JSON object using the entity schema (one value per path required).
3. Start the chosen sub-workflow once per entity, supplying the JSON as the replaceable
   input dataset.
4. Run up to `parallel_execution` workflow instances at the same time.
5. Stop with an error if any sub-workflow fails; see details in Activities.

Example entity mapping (illustrative):
Input schema paths: `label`, `id`  → JSON payload: `{ "label": "Example", "id": "123" }`

## Requirements

- The selected workflow must be in the same project as this task.
- The selected workflow must have exactly one replaceable input dataset.
- The input entities must be flat: each schema path may have at most one value per entity.

## Limitations

- Nested or multi-valued entities are not supported; multiple values per path raise an error.
- The replaceable dataset of the sub-workflow must be a JSON dataset.
- No circular dependency detection is performed.
- File processing is beta; correct `input_mime_type` and a file-accepting dataset in the
  sub-workflow are required.

## Troubleshooting

- "Need a connected input task": Connect one upstream task to provide entities.
- "Can process a single input only": Only one input port is supported.
- "Multiple values for entity path": Ensure each path has at most one value.
- "Workflow ... does not exist ... or is missing a single replaceable input dataset": Select
  a workflow in the same project with exactly one variable input.

## Typical Use Cases

- Per-record processing pipelines (e.g., validation, enrichment, export).
- Batch operations that require complex per-entity logic encapsulated in a workflow.
- Quality checks where each entity must pass through a dedicated validation workflow.
"""


@dataclass
class WorkflowExecution:
    """Represents the status of a concrete workflow execution"""

    task_id: str
    project_id: str
    entity: Entity
    schema: EntitySchema
    instance_id: str | None = None
    activity_id: str | None = None
    status: str = "QUEUED"
    is_running: bool = False
    raw: dict[str, str] | None = None
    execution_context: ExecutionContext | None = None
    logger: PluginLogger | None = None
    input_mime_type: str = ""

    @property
    def is_finished(self) -> bool:
        """True if the workflow is finished"""
        return self.status.upper() == "FINISHED"

    @property
    def is_queued(self) -> bool:
        """True if workflow is queued"""
        return self.status.upper() == "QUEUED"

    def entity_as_json_str(self) -> str:
        """Return the entity as a JSON string"""
        entity_as_dict = StartWorkflow.entity_to_dict(entity=self.entity, schema=self.schema)
        return json.dumps(entity_as_dict)

    def start(self) -> bool:
        """Start the workflow"""
        if self.logger:
            self.logger.info(f"Starting workflow execution: {self.entity_as_json_str()}")
        try:
            if self.execution_context:
                setup_cmempy_user_access(context=self.execution_context.user)
            if self.schema.type_uri == FileEntitySchema().type_uri and self.input_mime_type != "":
                response = execute_workflow_io(
                    project_name=self.project_id,
                    task_name=self.task_id,
                    input_file=self.entity.values[0][0],
                    input_mime_type=self.input_mime_type,
                )
                # workflows are NOT executed async at the moment
                self.status = "FINISHED"
                return True
            response = get_json(
                f"{config.get_di_api_endpoint()}/api/workflow/executeAsync/{self.project_id}/{self.task_id}",
                headers={"Content-Type": "application/json"},
                method="POST",
                data=self.entity_as_json_str(),
            )
        except HTTPError as error:
            if error.response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
                # 503 - no more execution capacity > no status change
                return False
            raise ValueError(str(error)) from error
        self.instance_id = response["instanceId"]
        self.activity_id = response["activityId"]
        self.update()
        return True

    def wait_until_finished(self) -> None:
        """Wait until the workflow is finished"""
        while self.is_running:
            self.update()
            sleep(1)

    def update(self) -> None:
        """Update the execution status"""
        if self.execution_context:
            setup_cmempy_user_access(context=self.execution_context.user)
        response = get_json(
            f"{config.get_di_api_endpoint()}/workspace/activities/status",
            params={
                "project": self.project_id,
                "task": self.task_id,
                "activity": self.activity_id,
                "instance": self.instance_id,
            },
        )
        self.status = response["statusName"]
        self.is_running = response["isRunning"]
        self.raw = response
        if self.logger:
            self.logger.debug(f"Updated Status: {self!s}")


@dataclass
class WorkflowExecutionList:
    """Workflow execution status list / registry"""

    statuses: list[WorkflowExecution]
    context: ExecutionContext
    logger: PluginLogger

    def __init__(self):
        self.statuses = []

    def execute(self, parallel_execution: int) -> None:
        """Execute all workflow executions"""
        while self.queued > 0 and not self.is_canceling():
            while self.running < parallel_execution and self.queued > 0 and not self.is_canceling():
                self.start_next()
            self.report()
            self.wait_until_finished()
        if self.is_canceling():
            self.logger.info("Execution canceled - stopping workflow processing")
        self.report()

    def start_next(self) -> bool:
        """Start the next workflow execution in queue"""
        all_queued = [_ for _ in self.statuses if _.is_queued]
        if not all_queued:
            return False
        next_in_queue: WorkflowExecution = all_queued[0]
        return next_in_queue.start()

    def wait_until_finished(self, polling_time: int = 1) -> None:
        """Wait until all running workflows are finished"""
        while self.running > 0 and not self.is_canceling():
            sleep(polling_time)
            self.update_running_status()
        if self.is_canceling():
            self.logger.info("Cancellation detected during polling - stopping workflow monitoring")

    def update_running_status(self) -> None:
        """Update status of running workflows"""
        for _ in self.statuses:
            if _.is_running:
                _.update()

    def append(self, status: WorkflowExecution) -> None:
        """Append a workflow execution to the list"""
        self.statuses.append(status)

    def report(self) -> None:
        """Report workflow statuses to the logger and/or execution report from context"""
        line = f"finished ({self.running} running, {self.queued} queued)"
        self.context.report.update(
            ExecutionReport(
                entity_count=self.finished,
                operation="start",
                operation_desc=line,
            )
        )
        self.logger.info(f"{self.finished} {line}")

    @property
    def running(self) -> int:
        """Returns the number of running workflows"""
        return len([_ for _ in self.statuses if _.is_running])

    @property
    def finished(self) -> int:
        """Returns the number of finished workflows"""
        return len([_ for _ in self.statuses if _.is_finished])

    @property
    def queued(self) -> int:
        """Returns the number of queued workflows"""
        return len([_ for _ in self.statuses if _.is_queued])

    def is_canceling(self) -> bool:
        """Check if the workflow execution context is in canceling state"""
        if self.context and hasattr(self.context, "workflow") and self.context.workflow:
            status = self.context.workflow.status()
            return str(status) == "Canceling"
        return False


@Plugin(
    label="Start Workflow per Entity",
    description="Loop over the output of a task and start a sub-workflow for each entity.",
    documentation=DOCUMENTATION,
    icon=Icon(package=__package__, file_name="loopwf.svg"),
    plugin_id="cmem_plugin_loopwf-task-StartWorkflow",
    parameters=[
        PluginParameter(
            name="workflow",
            label="Workflow",
            param_type=SuitableWorkflowParameterType(),
            description="Which workflow do you want to start per entity.",
        ),
        PluginParameter(
            name="parallel_execution",
            label="How many workflow jobs should run in parallel?",
            param_type=IntParameterType(),
            default_value=1,
        ),
        PluginParameter(
            name="forward_entities",
            label="Forward incoming entities to the output port?",
            param_type=BoolParameterType(),
            default_value=False,
        ),
        PluginParameter(
            name="input_mime_type",
            label="Mime-type for file by file processing (beta)",
            description="When working with file entities, setting this to a proper value will send"
            " the file to the"
            " workflow instead of the meta-data. Examples are: 'application/x-plugin-binaryFile',"
            " 'application/json', 'application/xml', 'text/csv', 'application/octet-stream' or"
            " 'application/x-plugin-excel'.",
            param_type=StringParameterType(),
            default_value="",
            advanced=True,
        ),
    ],
)
class StartWorkflow(WorkflowPlugin):
    """Start Workflow per Entity"""

    context: ExecutionContext
    executions: WorkflowExecutionList

    def __init__(
        self,
        workflow: str,
        parallel_execution: int = 1,
        forward_entities: bool = False,
        input_mime_type: str = "",
    ) -> None:
        self.workflow = workflow
        if parallel_execution < 1:
            raise ValueError("parallel_execution must be >= 1")
        self.parallel_execution = parallel_execution
        self.forward_entities = forward_entities
        self.input_mime_type = input_mime_type
        self.input_ports = FixedNumberOfInputs([FlexibleSchemaPort()])
        self.output_port = FlexibleSchemaPort() if forward_entities else None
        self.workflows_started = 0
        self.executions = WorkflowExecutionList()

    def start_workflows(self, inputs: Sequence[Entities]) -> Entities:
        """Start the workflows and return output entities"""
        input_entities = inputs[0].entities
        schema = inputs[0].schema
        self.executions.context = self.context
        self.executions.logger = self.log
        self.executions.report()
        for entity in input_entities:
            new_execution = WorkflowExecution(
                task_id=self.workflow,
                project_id=self.context.task.project_id(),
                entity=entity,
                schema=schema,
                execution_context=self.context,
                logger=self.log,
                input_mime_type=self.input_mime_type,
            )
            self.log.info(f"Got new entity: {new_execution.entity_as_json_str()}")
            self.executions.append(new_execution)
        self.executions.report()
        self.executions.execute(parallel_execution=self.parallel_execution)
        # remove execution via /workflow/workflows/{project}/{task}/execution/{executionId}

        return Entities(
            schema=schema,
            entities=iter([_.entity for _ in self.executions.statuses]),
        )

    def execute(
        self,
        inputs: Sequence[Entities],
        context: ExecutionContext,
    ) -> Entities | None:
        """Run the workflow operator."""
        self.log.info("Start execute")
        self.context = context
        self.validate_inputs(inputs=inputs)
        self.validate_workflow(workflow=self.workflow)
        output_entities = self.start_workflows(inputs=inputs)
        if self.forward_entities:
            self.log.info("All done ... forward entities")
            return output_entities
        self.log.info("All done ...")
        return None

    @staticmethod
    def validate_inputs(inputs: Sequence[Entities]) -> None:
        """Validate inputs."""
        inputs_count = len(inputs)
        if inputs_count == 0:
            raise exceptions.MissingInputError("Need a connected input task to get data from.")
        if inputs_count > 1:
            raise exceptions.TooManyInputsError("Can process a single input only.")

    def validate_workflow(self, workflow: str) -> None:
        """Validate a workflow (ID)"""
        current_project = self.context.task.project_id()
        setup_cmempy_user_access(context=self.context.user)
        suitable_workflows: dict[str, dict] = {
            f"{_['id']}": _
            for _ in get_workflows_io()
            if self.context.task.project_id() == _["projectId"] and len(_["variableInputs"]) == 1
        }
        if workflow not in suitable_workflows:
            raise exceptions.NoSuitableWorkflowError(
                f"Workflow '{workflow}' does not exist in project '{current_project}'"
                " or is missing a single replaceable input dataset."
            )
        self.log.info(str(suitable_workflows))

    @staticmethod
    def entity_to_dict(entity: Entity, schema: EntitySchema) -> dict:
        """Convert an entity to a dictionary, using the schema"""
        path: EntityPath
        values: Sequence[str]
        entity_dict = {}
        for path, values in zip(schema.paths, entity.values, strict=True):
            if len(values) > 1:
                raise exceptions.MultipleValuesError(f"Multiple values for entity path {path.path}")
            entity_dict[path.path] = values[0] if len(values) == 1 else ""
        return entity_dict
