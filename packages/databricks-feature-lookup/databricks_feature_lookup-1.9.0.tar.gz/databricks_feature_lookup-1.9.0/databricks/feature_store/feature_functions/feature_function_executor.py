from typing import Any, Callable, Dict, List, Set

import pandas as pd

from databricks.feature_store.entities.feature_functions_for_serving import (
    FeatureFunctionForServing,
    FeatureFunctionsForServing,
)
from databricks.feature_store.feature_functions.feature_function_loader import (
    FeatureFunctionLoader,
)
from databricks.feature_store.utils import feature_function_type_utils
from databricks.ml_features_common.entities.on_demand_column_info import (
    OnDemandColumnInfo,
)

OutputNameType = str


class _MaterializableFeatureFunction:
    """
    Encapsulates data required to evaluate a Feature Function, obtained from FeatureSpec and
    FeatureFunctionsForServing.
    """

    def __init__(
        self,
        ff_for_serving: FeatureFunctionForServing,
        odci: OnDemandColumnInfo,
        fn: Callable,
    ):
        self.odci = odci
        # fn is a Python function which can be called on UDF inputs to produce the uncasted UDF
        # output.
        self.fn = fn
        # column_args represents the list of columns that should be passed to fn.
        # For example, given a row of materialized feature columns, we evaluate the feature function by calling:
        #   fn(*[row[arg] for arg in column_args])
        self.column_args = [
            odci.input_bindings[input_param.name]
            for input_param in ff_for_serving.input_params
        ]
        self.return_data_type = ff_for_serving.data_type


class FeatureFunctionExecutor:
    """
    Library to execute Feature Functions on a pandas DataFrame in Databricks Model Serving.
    """

    def __init__(
        self,
        feature_functions_for_serving: FeatureFunctionsForServing,
        on_demand_column_infos: List[OnDemandColumnInfo],
    ):
        self.materializable_features = self._get_materializable_feature_metadata(
            feature_functions_for_serving, on_demand_column_infos
        )

    def execute_functions_for_rows(
        self, rows: List[Dict[str, Any]], functions_to_apply: List[OnDemandColumnInfo]
    ) -> List[Dict[str, Any]]:
        """
        Evaluates Feature Functions on a list of rows.
        """
        output_feat = [
            (info.output_name, self.materializable_features[info.output_name])
            for info in functions_to_apply
        ]
        for row in rows:
            for output, feat in output_feat:
                row[output] = feat.fn(*[row[arg] for arg in feat.column_args])
        return rows

    def execute_feature_functions(
        self, df: pd.DataFrame, functions_to_apply: List[OnDemandColumnInfo]
    ):
        """
        Evaluates Feature Functions on df.

        This method evaluates all Feature Functions passed to the class constructor. In the future,
        it may be extended to support calling only a subset of Feature Functions. This will be
        necessary, for example, if we support operations like TRANFORM-LOOKUP, where not all
        Feature Functions are applied in tandem.

        df is expected to include all function inputs.

        Beware that pandas may apply typecasting to df columns prior to executing the Feature
        Functions. Should the DataFrame contain columns of different type, the columns will be
        casted to the lowest common ancestor in the type tree. This is because a pd.Series is
        passed to _execute_on_demand_computation_on_row, and pd.Series is homogenously typed.

        For example, a DataFrame containing columns of np.int64 and np.float64 type will be casted
        to np.float64. A DataFrame containing columns of np.int64 and str type will be casted to
        object.

        In some cases, this may result in loss-of-precision (particularly at the large end of the
        int64 range). Should this be problematic to customers, we could alleviate this problem
        using one of the following approaches:
          a. Not use Pandas to apply Feature Functions, instead using eg dictionaries.
          b. Currying function application column-by-column, using single-column Pandas DataFrames
            or rows.

        The performance hit on these approaches is not yet clear, and probably requires profiling.

        :return: pd.DataFrame containing on-demand features. Number of columns == len(self.odci)
        """
        output_feat = [
            (info.output_name, self.materializable_features[info.output_name])
            for info in functions_to_apply
        ]

        def _execute_on_demand_computation_on_row(
            row: pd.core.series.Series,
        ) -> List[Any]:
            """
            Evaluates Feature Functions on the provided Pandas Series.
            """
            return [
                feat.fn(*[row[arg] for arg in feat.column_args])
                for output, feat in output_feat
            ]

        # Apply functions for each row of the df.
        uncasted_df = df.apply(
            _execute_on_demand_computation_on_row, axis=1, result_type="expand"
        )
        # Only select the function output columns.
        uncasted_df.columns = [info.output_name for info in functions_to_apply]
        return self._convert_output_types(uncasted_df)

    def _get_materializable_feature_metadata(
        self,
        feature_functions_for_serving: FeatureFunctionsForServing,
        on_demand_column_infos: List[OnDemandColumnInfo],
    ) -> Dict[OutputNameType, _MaterializableFeatureFunction]:
        """
        Re-structures the provided constructor inputs into a format more efficient for Feature
        Function evaluation:
          {on demand feature output name -> _MaterializableFeatureFunction}

        Every OnDemandColumnInfo UDF must be described by a FeatureFunctionForServing.

        For example:
            _get_materializable_feature_metadata(
              feature_functions_for_serving = [
                FeatureFunctionForServing(full_name="cat.sch.fn1", ...),
                FeatureFunctionForServing(full_name="cat.sch.fn2", ...),
              ],
              on_demand_column_infos = [
                OnDemandColumnInfo(udf_name="cat.sch.fn1", ...),
                OnDemandColumnInfo(udf_name="cat.sch.fn2", ...),
              ]
            )

        =>

            {
              "cat.sch.fn1":
                _MaterializableFeatureFunction(
                  FeatureFunctionForServing(full_name="cat.sch.fn1", ...),
                  OnDemandColumnInfo(udf_name="cat.sch.fn1", ...),
                  lambda x, y: ...
                ),
              "cat.sch.fn2":
                _MaterializableFeatureFunction(
                  FeatureFunctionForServing(full_name="cat.sch.fn2", ...),
                  OnDemandColumnInfo(udf_name="cat.sch.fn2", ...)
                  lambda a: ...
                )
            }
        """
        ff_for_serving_by_udf_name = {
            ff_for_serving.full_name: ff_for_serving
            for ff_for_serving in feature_functions_for_serving.ff_for_serving
        }
        fns_by_udf_name = FeatureFunctionLoader.load_feature_functions_map(
            feature_functions_for_serving
        )

        # Every OnDemandColumnInfo UDF must be described by a FeatureFunctionForServing. Because
        # multiple OnDemandColumnInfos may execute the same UDF, we have:
        # len(ff_for_serving_by_udf_name) >= len(odci_by_udf_name)
        # Return a _MaterializableFeatureFunction for each OnDemandColumnInfo
        return {
            odci.output_name: _MaterializableFeatureFunction(
                ff_for_serving=ff_for_serving_by_udf_name[odci.udf_name],
                odci=odci,
                fn=fns_by_udf_name[odci.udf_name],
            )
            for odci in on_demand_column_infos
        }

    def _convert_output_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Casts pandas DataFrame `df` to the expected output data types of FeatureFunctions.
        Expects all computed FeatureFunction outputs to be columns in `df`.

        :param df: pandas DataFrame with uncasted FeatureFunctions outputs.
        :return: pandas DataFrame casted to data types specified by FeatureFunction outputs.
        """
        spark_schema = [
            (output_name, self.materializable_features[output_name].return_data_type)
            for output_name in df.columns
        ]
        return feature_function_type_utils.cast_pandas_df(
            df=df, spark_schema=spark_schema
        )
