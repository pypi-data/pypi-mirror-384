"""jq transform operator"""

from collections.abc import Sequence

import jq
from cmem_plugin_base.dataintegration.description import (
    Plugin,
    PluginParameter,
)
from cmem_plugin_base.dataintegration.plugins import TransformPlugin
from cmem_plugin_base.dataintegration.types import BoolParameterType

from cmem_plugin_jq.common import JQ_INTRO

jq_expression_default = "."
single_item_as_string_default = True


@Plugin(
    label="jq",
    plugin_id="cmem-plugin-jq-transform",
    description="Process a JSON path with a jq filter / program.",
    documentation=f"""
{JQ_INTRO}
""",
    parameters=[
        PluginParameter(
            name="jq_expression",
            label="jq Expression",
            description="The jq program to apply to the input JSON string.",
            default_value=jq_expression_default,
        ),
        PluginParameter(
            name="single_item_as_string",
            param_type=BoolParameterType(),
            label="Output list with one item as string",
            default_value=single_item_as_string_default,
            advanced=True,
        ),
    ],
)
class JqTransformOperator(TransformPlugin):
    """jq Transform Operator"""

    def __init__(
        self,
        jq_expression: str = jq_expression_default,
        single_item_as_string: bool = single_item_as_string_default,
    ):
        self.compiled = jq.compile(jq_expression)
        self.single_item_as_string = single_item_as_string

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Process the inputs with jq"""
        if not inputs:
            raise ValueError("No inputs provided.")
        if len(inputs) > 1:
            raise ValueError("The operator cannot handle more than one input.")
        return [self.do_jq(input_string) for input_string in inputs[0]]

    def do_jq(self, input_string: str) -> str:
        """Run jq with a given input string"""
        result = self.compiled.input_text(input_string).all()
        if len(result) == 1 and self.single_item_as_string:
            return str(result[0])
        return str(result)
