from functools import reduce
from typing import Any, Dict, List, Optional

import pandas as pd

from databricks.feature_store.entities.feature_table_metadata import (
    FeatureTableMetadata,
)
from databricks.feature_store.feature_functions.feature_function_executor import (
    FeatureFunctionExecutor,
)
from databricks.feature_store.online_lookup_client import OnlineLookupClient
from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.feature_store.utils.latency_debugger import LatencyDebugger
from databricks.feature_store.utils.lookup_key_utils import LookupKeyType
from databricks.ml_features_common.entities.data_type import DataType
from databricks.ml_features_common.entities.feature_column_info import FeatureColumnInfo
from databricks.ml_features_common.entities.feature_spec import FeatureSpec
from databricks.ml_features_common.entities.on_demand_column_info import (
    OnDemandColumnInfo,
)
from databricks.ml_features_common.entities.online_feature_table import (
    PrimaryKeyDetails,
)
from databricks.ml_features_common.utils.data_type_utils import (
    deserialize_default_value_primitive_type,
)
from databricks.ml_features_common.utils.feature_spec_utils import (
    COLUMN_INFO_TYPE_FEATURE,
    COLUMN_INFO_TYPE_ON_DEMAND,
    COLUMN_INFO_TYPE_SOURCE,
    get_feature_execution_groups,
)


class _PgTableFetcher:
    """
    Each (feature_table, lookup_keys) pair is associated with a single _PgTableFetcher instance.
    The fetcher is responsible for fetching data from the online store and filling in default values.
    """

    def __init__(
        self,
        lookup_key: LookupKeyType,
        primary_keys: List[PrimaryKeyDetails],
        feature_column_infos: List[FeatureColumnInfo],
        lookup_client: OnlineLookupClient,
        feature_type_mapping: Dict[str, DataType],
        latency_debugger: LatencyDebugger,
    ):
        """
        Args:
            lookup_key: A list of input column names. The ordering needs to match the ordering of the primary keys.
            primary_keys: Primary keys defined in the online table
            feature_columns: A list of feature columns to fetch
            lookup_client: Lookup client for the online table
            feature_type_mapping: Mapping from feature name to data type.
        """
        self.lookup_key = lookup_key
        self.lookup_client = lookup_client
        self.feature_column_infos = feature_column_infos
        self._primary_key_names = [pk.name for pk in primary_keys]
        self._feature_names = [fci.feature_name for fci in feature_column_infos]
        self._latency_debugger = latency_debugger
        self._default_values = {
            fci.feature_name: deserialize_default_value_primitive_type(
                fci.default_value_str, feature_type_mapping[fci.feature_name]
            )
            for fci in feature_column_infos
            if fci.default_value_str is not None
        }
        self._renaming = {
            fci.feature_name: fci.output_name
            for fci in feature_column_infos
            if fci.feature_name != fci.output_name
        }

    def _build_lookup_key_list(self, rows: List[Dict[str, Any]]) -> LookupKeyList:
        return LookupKeyList(
            columns=self._primary_key_names,
            rows=[[row[lookup_key] for lookup_key in self.lookup_key] for row in rows],
        )

    def fetch(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        lookup_key_list = self._build_lookup_key_list(rows)
        self._latency_debugger.add_latency("pg_build_lookup_key_list")
        lookup_results = self.lookup_client.lookup_feature_dicts(
            lookup_key_list, self._feature_names
        )
        self._latency_debugger.add_latency("pg_lookup_feature_dicts")
        # Fill in default values.
        for i, lookup_result in enumerate(lookup_results):
            for feature_name, default_value in self._default_values.items():
                if lookup_result.get(feature_name, None) is None:
                    lookup_results[i][feature_name] = default_value
        # Rename columns.
        if self._renaming:
            for i, lookup_result in enumerate(lookup_results):
                lookup_results[i] = {
                    self._renaming.get(k, k): v for k, v in lookup_result.items()
                }
        return lookup_results


class PostgresFetcher:
    def __init__(
        self,
        feature_spec: FeatureSpec,
        lookup_clients: Dict[str, OnlineLookupClient],
        ft_metadatas: Dict[str, FeatureTableMetadata],
        feature_function_executor: Optional[FeatureFunctionExecutor],
        latency_debugger: LatencyDebugger,
    ):
        """
        Initialize the PostgresFetcher.
        Args:
            feature_spec: FeatureSpec
            lookup_clients: feature table name -> lookup client
            ft_metadatas: feature table name -> feature_table_metadata
        """
        self.feature_spec = feature_spec
        self.feature_function_executor = feature_function_executor
        # FeatureTable (name, lookup_key) -> fetcher
        # lookup_key is a list of input column names.
        self.table_fetchers = {}
        # The desired output columns in the final result. Other columns should be filtered out.
        self._output_names = [
            ci.output_name for ci in feature_spec.column_infos if ci.include
        ]
        # All columns in the feature spec. Including input and output columns.
        self._all_column_names = [ci.output_name for ci in feature_spec.column_infos]

        self._needs_dag_execution = (
            feature_spec.has_dag() or len(feature_spec.on_demand_column_infos) > 0
        )
        # Execution group is calcualted based on input columns and the feature spec.
        # cached execution groups are used if the input columns are the same.
        self._execution_groups = None
        self._input_columns = None
        self._latency_debugger = latency_debugger
        for ft, ft_metadata in ft_metadatas.items():
            for (
                lookup_key,
                feature_column_infos,
            ) in ft_metadata.feature_col_infos_by_lookup_key.items():
                self.table_fetchers[(ft, lookup_key)] = _PgTableFetcher(
                    lookup_key,
                    ft_metadata.online_ft.primary_keys,
                    feature_column_infos,
                    lookup_clients[ft],
                    ft_metadata.get_table_feature_type_mapping(),
                    latency_debugger,
                )

    def _lookup_feature_group(
        self, input_rows: List[Dict[str, Any]], features: List[FeatureColumnInfo]
    ) -> List[dict[str, Any]]:
        """
        Lookup features in an execution group.
        """
        # 1. group features by (feature_table, lookup_key)
        feature_groups = {}
        for feature in features:
            # Convert lookup_key list to tuple for use as dictionary key
            lookup_key_tuple = tuple(feature.lookup_key)
            group_key = (feature.table_name, lookup_key_tuple)

            if group_key not in feature_groups:
                feature_groups[group_key] = []
            feature_groups[group_key].append(feature)

        # 2. lookup features in each group
        group_results = []
        for (table_name, lookup_key_tuple), group_features in feature_groups.items():
            # Get the appropriate table fetcher
            fetcher = self.table_fetchers.get((table_name, lookup_key_tuple))
            if fetcher is None:
                raise ValueError(
                    f"No fetcher found for table {table_name} with lookup key {lookup_key_tuple}"
                )

            # Fetch features for this group
            group_result = fetcher.fetch(input_rows)
            group_results.append(group_result)

        # 3. merge results by rows
        if not group_results:
            # If no feature groups, return input rows as-is
            return input_rows

        # Merge all group results with input rows
        merged_results = []
        for i in range(len(input_rows)):
            merged_row = {}
            # merge features from all groups for this row
            for group_result in group_results:
                if i < len(group_result):
                    merged_row.update(group_result[i])
            # override with values from input_rows (input values take precedence)
            merged_row.update(input_rows[i])
            merged_results.append(merged_row)

        # 4. return the result
        return merged_results

    def _lookup_with_dag(self, df: pd.DataFrame) -> List[dict[str, Any]]:
        """
        Lookup features with a DAG.
        """
        if self._execution_groups is None or self._input_columns != df.columns.tolist():
            self._input_columns = df.columns.tolist()
            self._execution_groups = get_feature_execution_groups(self.feature_spec, df)

        # Start with input data
        current_rows = df.to_dict(orient="records")

        for group in self._execution_groups:
            if group.type == COLUMN_INFO_TYPE_SOURCE:
                # no action required for source columns
                continue
            elif group.type == COLUMN_INFO_TYPE_FEATURE:
                # Lookup features for this execution group
                current_rows = self._lookup_feature_group(current_rows, group.features)
            elif group.type == COLUMN_INFO_TYPE_ON_DEMAND:
                # Apply functions for this execution group
                current_rows = (
                    self.feature_function_executor.execute_functions_for_rows(
                        current_rows, group.features
                    )
                )

        return current_rows

    def lookup_features(self, df: pd.DataFrame) -> List[dict[str, Any]]:
        """
        Lookup features.

        Args:
            df: DataFrame with lookup keys.

        Returns:
            List of dictionaries with features.
        """
        if self._needs_dag_execution:
            all_results = self._lookup_with_dag(df)
        else:
            input_rows = df.to_dict(orient="records")
            results = [
                fetcher.fetch(input_rows) for fetcher in self.table_fetchers.values()
            ]
            # Merge all results by rows.
            all_results = [
                reduce(lambda a, b: {**a, **b}, group, {})
                for group in zip(*results, input_rows)
            ]
        if all_results and len(self._all_column_names) == len(self._output_names):
            return all_results
        else:
            # TODO[ML-55717]: Optimize the filtering performance.
            # filter out the columns that are excluded.
            return [
                {k: v for k, v in result.items() if k in self._output_names}
                for result in all_results
            ]

    def get_model_input_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get the model input DataFrame.
        """
        feature_values = self.lookup_features(df)
        # convert the feature_values to a DataFrame
        return pd.DataFrame(
            feature_values,
            columns=self._output_names,  # specify the column ordering
        )
