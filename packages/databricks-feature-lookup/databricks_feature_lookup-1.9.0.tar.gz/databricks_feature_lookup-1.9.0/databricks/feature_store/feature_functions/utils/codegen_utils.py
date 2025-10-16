import textwrap
import typing

from databricks.feature_store.entities.feature_functions_for_serving import (
    FeatureFunctionForServing,
    FeatureFunctionParameterInfo,
    FeatureFunctionsForServing,
)

INDENT = " " * 4


class CodegenUtils:
    """
    This utility class wraps functions used to generate the code required to evalute Feature
    Functions in Model Serving.
    """

    @staticmethod
    def _gen_params(param_infos: typing.List[FeatureFunctionParameterInfo]) -> str:
        """
        Generate a list of parameters for generated function
        """
        return ", ".join([param_info.name for param_info in param_infos])

    @staticmethod
    def _indent(body: str) -> str:
        return textwrap.indent(body, prefix=INDENT, predicate=lambda _: True)

    @staticmethod
    def generate_function(
        fn_name: str, ff_for_serving: FeatureFunctionForServing
    ) -> str:
        """
        Generates Python3 code containing a function with name `fn_name`, and parameters +
        definition as specfieid by FeatureFunctionForServing.

        For example:
        generate_function(
          "my_cool_function",
          FeatureFunctionForServing(
            ...,
            routine_definition="return a + b",
            input_params = [
              FeatureFunctionParameterInfo(name="a"),
              FeatureFunctionParameterInfo(name="b")
            ]

        =>

        '''\
        def my_cool_function(a, b):
          return a + b
        '''

        For more examples, see tests.
        """
        params_str = CodegenUtils._gen_params(ff_for_serving.input_params)
        indented_body = CodegenUtils._indent(ff_for_serving.routine_definition)
        # We don't use dedent to prettify the below since it swallows newlines.
        return f"""\
def {fn_name}({params_str}):
{indented_body}
"""
