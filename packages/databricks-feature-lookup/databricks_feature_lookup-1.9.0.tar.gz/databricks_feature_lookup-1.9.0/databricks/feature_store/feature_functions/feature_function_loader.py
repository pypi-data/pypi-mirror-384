import typing

from databricks.feature_store.entities.feature_functions_for_serving import (
    FeatureFunctionForServing,
    FeatureFunctionParameterInfo,
    FeatureFunctionsForServing,
)
from databricks.feature_store.feature_functions.utils.codegen_utils import CodegenUtils

# USER_FUNC_NAME is used as the function name of the Feature Function UDF in generated code. It
# is the same value used by Safe Spark when executing Python UDFs:
# https://github.com/databricks/runtime/blob/f976bbb0f71077c5f79015ffa87d930b249061ab/safespark/udf/py/udfserver/server.py#L138
# We assume that the user does not have a global value with conflicting name in their UDF
# routine_definition.
USER_FUNC_NAME = "_udf_handler_func_entry"


class FeatureFunctionLoader:
    """
    This class transforms Feature Functions defined by FeatureFunctionsForServing into Python
    functions.

    Logic to transform FeatureFunctionForServing function definition strings into Python callable
    objects is run within a separate scope from the calling environment. As such, closures are not
    supported.

    The function is executed within the same Python environment as the caller, so all packages
    installed in the Python environment are available.
    """

    @staticmethod
    def load_feature_function(
        ff_for_serving: FeatureFunctionForServing,
    ) -> typing.Callable:
        """
        Loads a single Feature Function
        """
        globals = {}
        generated_code = CodegenUtils.generate_function(USER_FUNC_NAME, ff_for_serving)
        # `exec` will execute code outside of the local + global scope, and dumps global variables
        # into `globals`. The generated code declares a global USER_FUNC_NAME equal to the Python
        # function. We can then extract this function from the `globals`
        exec(generated_code, globals)
        return globals[USER_FUNC_NAME]

    @staticmethod
    def load_feature_functions_map(
        ffs_for_serving: FeatureFunctionsForServing,
    ) -> typing.Dict[str, typing.Callable]:
        """
        Loads all FeatureFunctions included in ffs_for_serving.

        Returns a dictionary mapping function name to function.

        load_feature_functions_map(
          FeatureFunctionsForServing(
            ff_for_servign = [
              FeatureFunctionForServing("cat.sch.fn1", ...),
              FeatureFunctionForServing("cat.sch.fn2", ...),
            ]
          )
        )

        =>

        {
          "cat.sch.fn1": fn1,
          "cat.sch.fn2": fn2
        }

        Where fn1 and fn2 are functions.
        """
        return {
            ff_for_serving.full_name: FeatureFunctionLoader.load_feature_function(
                ff_for_serving
            )
            for ff_for_serving in ffs_for_serving.ff_for_serving
        }
