"""jq Workflow Task"""

import gzip
import io
import json
from collections.abc import Sequence
from contextlib import suppress
from tempfile import NamedTemporaryFile

import jq
from cmem_plugin_base.dataintegration.context import ExecutionContext, ExecutionReport
from cmem_plugin_base.dataintegration.description import Icon, Plugin, PluginAction, PluginParameter
from cmem_plugin_base.dataintegration.entity import (
    Entities,
)
from cmem_plugin_base.dataintegration.parameter.code import JsonCode
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.ports import FixedNumberOfInputs, FixedSchemaPort
from cmem_plugin_base.dataintegration.typed_entities.file import File, FileEntitySchema, LocalFile
from cmem_plugin_base.dataintegration.typed_entities.typed_entities import TypedEntitySchema
from cmem_plugin_base.dataintegration.utils import setup_cmempy_user_access

from cmem_plugin_jq.common import JQ_INTRO

jq_expression_default = "."


def _is_gzip(stream: io.BufferedReader) -> bool:
    """Check if Gzip by peeking at the first two bytes"""
    head = stream.read(2)
    stream.seek(0)
    return head == b"\x1f\x8b"


@Plugin(
    label="jq",
    plugin_id="cmem-plugin-jq-workflow",
    description="Process a JSON document with a jq filter / program.",
    documentation=f"""
{JQ_INTRO}
""",
    icon=Icon(package=__package__, file_name="jq.svg"),
    actions=[
        PluginAction(
            name="validate_expression",
            label="Validate expression",
            description="Compiles the expression and executes it on the example"
            " data (see advanced option section).",
        )
    ],
    parameters=[
        PluginParameter(
            name="jq_expression",
            label="jq Expression",
            description="The jq program to apply to the input JSON string.",
            default_value=jq_expression_default,
        ),
        PluginParameter(
            name="validation_source",
            label="JSON source which can be used with the validate expression action",
            default_value=JsonCode(""),
            advanced=True,
        ),
    ],
)
class JqWorkflowTask(WorkflowPlugin):
    """jq Workflow Task"""

    context: ExecutionContext
    validation_source: str
    schema: TypedEntitySchema = FileEntitySchema()

    def __init__(self, jq_expression: str, validation_source: JsonCode) -> None:
        self.compiled = jq.compile(jq_expression)
        self.validation_source = validation_source.code
        self.output_port = FixedSchemaPort(schema=self.schema)
        self.input_ports = FixedNumberOfInputs([FixedSchemaPort(schema=self.schema)])

    def validate_expression(self) -> str:
        """Compiles the expression and executes it on the example data"""
        output = f"- jq expression '`{self.compiled.program_string}`' is valid."
        if self.validation_source != "":
            output += (
                "\n- Result of the execution of this expression against the validation source:\n"
            )
            output += f"``` json\n{self.jq_single_or_list(self.validation_source)}\n```"
        return output

    def execute(
        self,
        inputs: Sequence[Entities],
        context: ExecutionContext,
    ) -> Entities:
        """Run the workflow operator."""
        if not inputs:
            raise ValueError("No Input - Please connect a JSON dataset to the input port.")
        files: list[File] = []
        self.context = context
        for entity in inputs[0].entities:
            with suppress(AttributeError):
                if context.workflow.status() == "Canceling":
                    break
            setup_cmempy_user_access(context.user)
            files.append(self.do_jq(self.schema.from_entity(entity)))
            context.report.update(
                ExecutionReport(
                    entity_count=len(files),
                    operation="processed",
                    operation_desc="file processed" if len(files) == 1 else "files processed",
                )
            )

        entities = [self.schema.to_entity(file) for file in files]
        return Entities(entities=iter(entities), schema=self.schema)

    def jq_single_or_list(self, input_text: str) -> str:
        """Run jq and return a JSON string"""
        result = self.compiled.input_text(input_text).all()
        return json.dumps(result[0], indent=2) if len(result) == 1 else json.dumps(result, indent=2)

    def do_jq(self, file: File) -> File:
        """Run jq with a given input file (and output the result file)"""
        with file.read_stream(self.context.task.project_id()) as input_file:
            # Wrap input in buffered stream if needed
            buffered = io.BufferedReader(input_file)
            # Check if Gzip by peeking at the first two bytes
            if _is_gzip(buffered):
                decompressed_stream = gzip.GzipFile(fileobj=buffered)
            else:
                decompressed_stream = buffered  # type: ignore[assignment]

            input_text = decompressed_stream.read().decode("utf-8")
            json_string = self.jq_single_or_list(input_text)
        with NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as output_file:
            output_file.write(json_string)
            return LocalFile(path=output_file.name)
