import inspect
import itertools
import logging
import os
import time
from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import mlflow
import pandas as pd
from mlflow.entities import SpanType
from mlflow.utils import databricks_utils
from packaging import version

from databricks.feature_store.entities.feature_functions_for_serving import (
    FeatureFunctionsForServing,
)
from databricks.feature_store.entities.feature_table_metadata import (
    FeatureTableMetadata,
)
from databricks.feature_store.feature_functions.feature_function_executor import (
    FeatureFunctionExecutor,
)
from databricks.feature_store.feature_lookup_version import VERSION
from databricks.feature_store.online_lookup_client import (
    OnlineLookupClient,
    can_use_brickstore_http_gateway,
    is_primary_key_lookup,
    tables_share_dynamodb_access_keys,
)
from databricks.feature_store.postgres_fetcher import PostgresFetcher
from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.feature_store.utils.delta_sharing_utils import get_catalog_name_override
from databricks.feature_store.utils.lakebase_constants import (
    FEATURE_SERVING_HP,
    LAKEBASE_USER,
)
from databricks.feature_store.utils.latency_debugger import LatencyDebugger
from databricks.feature_store.utils.logging_utils import get_logger
from databricks.feature_store.utils.lookup_key_utils import (
    LookupKeyType,
    get_primary_key_list,
)
from databricks.feature_store.utils.metrics_utils import (
    OVERRIDEN_FEATURE_COUNT,
    LookupClientMetrics,
    lookup_call_maybe_with_metrics,
)
from databricks.feature_store.utils.timeout_utils import (
    TOTAL_REQUEST_TIMEOUT_SECONDS,
    timeout,
)
from databricks.feature_store.utils.trace_utils import (
    is_feature_tracing_enabled,
    trace_latency,
)
from databricks.ml_features_common import mlflow_model_constants
from databricks.ml_features_common.entities.data_type import DataType
from databricks.ml_features_common.entities.feature_column_info import FeatureColumnInfo
from databricks.ml_features_common.entities.feature_spec import FeatureSpec
from databricks.ml_features_common.entities.feature_tables_for_serving import (
    FeatureTablesForServing,
)
from databricks.ml_features_common.entities.on_demand_column_info import (
    OnDemandColumnInfo,
)
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
    PrimaryKeyDetails,
)
from databricks.ml_features_common.entities.store_type import StoreType
from databricks.ml_features_common.mlflow_model_constants import _NO_RESULT_TYPE_PASSED
from databricks.ml_features_common.protos.feature_store_serving_pb2 import (
    DataType as ProtoDataType,
)
from databricks.ml_features_common.utils.data_type_utils import (
    deserialize_default_value_to_data_type,
)
from databricks.ml_features_common.utils.feature_spec_utils import (
    COLUMN_INFO_TYPE_FEATURE,
    COLUMN_INFO_TYPE_ON_DEMAND,
    COLUMN_INFO_TYPE_SOURCE,
    get_feature_execution_groups,
)
from databricks.ml_features_common.utils.uc_utils import (
    get_feature_spec_with_full_table_names,
    get_feature_spec_with_reformat_full_table_names,
)

# The provisioner of this model is expected to set an environment variable with the path to a
# feature_tables_for_serving.dat file.
FEATURE_TABLES_FOR_SERVING_FILEPATH_ENV = "FEATURE_TABLES_FOR_SERVING_FILEPATH"
# should match LOOKUP_CLIENT_INSTRUMENTATION_ENABLED_ENV in
# model-serving/model-serving-common/src/main/scala/com/databricks/mlflow/utils/serving/FeatureStoreConstants.scala
# this was recently updated to a new value to prevent triggering issues with old version of lookup client when instrumentation is enabled (ML-48928)
LOOKUP_CLIENT_INSTRUMENTATION_ENABLED_ENV = "ENABLE_LOOKUP_CLIENT_INSTRUMENTATION"
# should match LOOKUP_CLIENT_FEATURE_FUNCTION_EVALUATION_ENABLED_ENV in
# model-serving/model-serving-common/src/main/scala/com/databricks/mlflow/utils/serving/FeatureStoreConstants.scala
LOOKUP_CLIENT_FEATURE_FUNCTION_EVALUATION_ENABLED_ENV = (
    "LOOKUP_CLIENT_FEATURE_FUNCTION_EVALUATION_ENABLED"
)
LOOKUP_PERFORMANCE_DEBUG_ENABLED = "LOOKUP_PERFORMANCE_DEBUG_ENABLED"
# Env var to tell if the served entity is a Model or a FeatureSpec
ENV_SERVABLE_TYPE = "SERVABLE_TYPE"

_logger = get_logger(__name__, log_level=logging.INFO)


def _load_raw_model(path):
    raw_model_path = os.path.join(path, mlflow_model_constants.RAW_MODEL_FOLDER)
    return mlflow.pyfunc.load_model(raw_model_path)


class _FeatureStoreModelWrapper:
    def __init__(
        self, path: str, current_time_seconds_fn: Callable[[], float] = time.time
    ):
        _logger.info(f"Initializing feature store lookup client: {VERSION}")
        self._check_support()
        feature_tables_for_serving = self._load_feature_tables_for_serving()
        feature_functions_for_serving = None
        self.has_feature_functions = False
        self._latency_debugger = LatencyDebugger(current_time_seconds_fn)

        if self._is_lookup_client_feature_function_evaluation_enabled():
            self.has_feature_functions = self._has_feature_functions(path)
            if self.has_feature_functions:
                feature_function_dir = os.path.join(
                    path, mlflow_model_constants.FEATURE_STORE_INTERNAL_DATA_DIR
                )
                feature_functions_for_serving = FeatureFunctionsForServing.load(
                    feature_function_dir
                )

        self.raw_model = _load_raw_model(path)

        # Reformat local metastore 3L tables to 2L. Non-local metastore 3L tables and 2L tables are unchanged.
        # This guarantees table name consistency between feature_spec and feature_tables_for_serving.
        # https://docs.google.com/document/d/1x_V9GshlnoAAFFCuDsXWdJVtop9MG2HWTUo5IK_1mEw
        original_feature_spec = FeatureSpec.load(path)

        catalog_name_override = get_catalog_name_override(
            original_feature_spec,
            feature_tables_for_serving,
            feature_functions_for_serving,
        )

        # We call get_feature_spec_with_full_table_names to append the default metastore to 2L names,
        # as get_feature_spec_with_reformat_full_table_names expects full 3L table names and throws otherwise.
        # TODO (ML-26593): Consolidate this into a single function that allows either 2L/3L names.
        feature_spec_with_full_table_names = get_feature_spec_with_full_table_names(
            original_feature_spec, catalog_name_override
        )
        self.feature_spec = get_feature_spec_with_reformat_full_table_names(
            feature_spec_with_full_table_names
        )

        self.ft_metadata = self._get_ft_metadata(
            self.feature_spec, feature_tables_for_serving
        )
        self._validate_ft_metadata(self.ft_metadata)
        # Print the table names for users to validate.
        lakebase_tables = []
        for _, meta in self.ft_metadata.items():
            if (
                meta.online_ft.online_store.store_type
                == StoreType.DATABRICKS_ONLINE_STORE
            ):
                lakebase_tables.append(meta.online_ft.online_feature_table_name)
        if len(lakebase_tables) > 0:
            _logger.info(
                f"Tables in Databricks Online Feature Store: {lakebase_tables}"
            )
        self.eligible_for_pgsql_connection = self._eligible_for_pgsql_connection()
        self.is_model_eligible_for_batch_lookup = (
            self._is_model_eligible_for_batch_lookup(self.ft_metadata)
        )
        if (
            self.eligible_for_pgsql_connection
            or not self.is_model_eligible_for_batch_lookup
        ):
            self.ft_to_lookup_client = self._create_lookup_clients(
                self.ft_metadata, self.eligible_for_pgsql_connection
            )
        else:
            self.batch_lookup_client = self._create_batch_lookup_client(
                self.ft_metadata
            )
        if self.has_feature_functions:
            self.feature_function_executor = FeatureFunctionExecutor(
                feature_functions_for_serving,
                self.feature_spec.on_demand_column_infos,
            )
        else:
            self.feature_function_executor = None
        if self.eligible_for_pgsql_connection:
            self.pg_sql_fetcher = PostgresFetcher(
                self.feature_spec,
                self.ft_to_lookup_client,
                self.ft_metadata,
                self.feature_function_executor,
                self._latency_debugger,
            )
        self.table_feature_data_type_mapping = self._map_feature_to_data_type(
            self.ft_metadata
        )

    def _map_feature_to_data_type(
        self, ft_metadatas: Dict[str, FeatureTableMetadata]
    ) -> Dict[str, Dict[str, DataType]]:
        """
        Maps feature names to their data types. This is used to deserialize the default values
        of features in the FeatureSpec.
        """
        table_feature_data_type_mapping = defaultdict(
            lambda: dict()
        )  # oft_name -> feature_name -> data_type
        for ft_name, ft_meta in ft_metadatas.items():
            oft = ft_meta.online_ft
            for feature_detail in oft.features:
                table_feature_data_type_mapping[
                    oft.online_feature_table_name
                ] = ft_meta.get_table_feature_type_mapping()
        return table_feature_data_type_mapping

    def _has_feature_functions(self, path):
        feature_function_dir = os.path.join(
            path, mlflow_model_constants.FEATURE_STORE_INTERNAL_DATA_DIR
        )
        return os.path.isfile(
            os.path.join(feature_function_dir, FeatureFunctionsForServing.DATA_FILE)
        )

    # true if all feature tables using DynamoDB under same authorization (ie same region and keys)
    def _is_model_eligible_for_batch_lookup(
        self, ft_metadata: Dict[str, FeatureTableMetadata]
    ):
        online_feature_tables = [meta.online_ft for _, meta in ft_metadata.items()]
        return (
            tables_share_dynamodb_access_keys(online_feature_tables)
            and is_primary_key_lookup(online_feature_tables)
        ) or can_use_brickstore_http_gateway(online_feature_tables)

    @staticmethod
    def _load_feature_tables_for_serving() -> FeatureTablesForServing:
        return FeatureTablesForServing.load(
            path=os.getenv(FEATURE_TABLES_FOR_SERVING_FILEPATH_ENV)
        )

    @staticmethod
    def _is_lookup_client_instrumentation_enabled() -> bool:
        # environment variables stored as string, rather than boolean
        return os.getenv(LOOKUP_CLIENT_INSTRUMENTATION_ENABLED_ENV) == "true"

    @staticmethod
    def _is_lookup_performance_debug_enabled() -> bool:
        # environment variables stored as string, rather than boolean
        return os.getenv(LOOKUP_PERFORMANCE_DEBUG_ENABLED) == "true"

    @staticmethod
    def _is_lookup_client_feature_function_evaluation_enabled() -> bool:
        return (
            os.getenv(LOOKUP_CLIENT_FEATURE_FUNCTION_EVALUATION_ENABLED_ENV) == "true"
        )

    @staticmethod
    def _check_support():
        if (
            databricks_utils.is_in_databricks_notebook()
            or databricks_utils.is_in_databricks_job()
        ):
            raise NotImplementedError(
                "Feature Store packaged models cannot be loaded with MLflow APIs. For batch "
                "inference, use FeatureStoreClient.score_batch."
            )

    @staticmethod
    def _validate_ft_metadata(ft_metadata: Dict[str, FeatureTableMetadata]):
        for ft, meta in ft_metadata.items():
            for lookup_key in meta.feature_col_infos_by_lookup_key.keys():
                if len(lookup_key) != len(meta.online_ft.primary_keys):
                    raise Exception(
                        f"Internal error: Online feature table has primary keys "
                        f"{meta.online_ft.primary_keys}, however FeatureSpec specifies "
                        f"{len(lookup_key)} lookup_keys: {lookup_key}."
                    )

    @staticmethod
    def _current_time_ms():
        # consider switching to time.perf_counter if more precise result is needed.
        return int(time.time() * 1000)

    def _create_lookup_clients(
        self, ft_metadata: Dict[str, FeatureTableMetadata], eligible_for_pgsql: bool
    ) -> Dict[str, OnlineLookupClient]:
        ft_to_lookup_client = {}
        for ft, meta in ft_metadata.items():
            ft_to_lookup_client[ft] = OnlineLookupClient(
                meta.online_ft, eligible_for_pgsql
            )
        return ft_to_lookup_client

    def _create_batch_lookup_client(
        self, ft_metadata: Dict[str, FeatureTableMetadata]
    ) -> Optional[OnlineLookupClient]:
        """
        Creates and returns an OnlineLookupClient for batch lookup, or None if `ft_metadata` is
        empty.
        """
        if not ft_metadata:
            return None
        online_fts = []
        for ft, meta in ft_metadata.items():
            online_fts.append(meta.online_ft)
        # Batch lookup is not supported for PGSQL connection
        return OnlineLookupClient(online_fts, eligible_for_pgsql=False)

    @trace_latency("feature_lookup")
    def _monitored_augment_with_materialized_features(
        self,
        df: pd.DataFrame,
        features_to_lookup: List[FeatureColumnInfo],
        partially_overridden_feature_output_names: List[str],
        *,
        output_metrics: LookupClientMetrics = None,
    ):
        augment_with_materialized_features = lookup_call_maybe_with_metrics(
            self._augment_with_materialized_features,
            output_metrics,
            measuring_e2e_latency=True,
        )

        # Add materialized features to `df`. This call does not do input column filtering, which is
        # important as Feature Functions may require inputs with include=False, so filtering must
        # be done after Feature Function execution. See _augment_with_materialized_features
        # docstring for details.
        return augment_with_materialized_features(
            df,
            features_to_lookup,
            partially_overridden_feature_output_names,
            metrics=output_metrics,
        )

    @trace_latency("feature_function")
    def _augment_with_on_demand_features(self, df, functions_to_apply):
        if (
            self._is_lookup_client_feature_function_evaluation_enabled()
            and self.has_feature_functions
        ):
            # Includes fully and partially overridden columns in this iteration.
            df_columns_set = set(df.columns)
            override_columns = [
                f.output_name
                for f in functions_to_apply
                if f.output_name in df_columns_set
            ]
            if override_columns:
                overrides = df[override_columns]
                # May contain partially overridden columns that will be used in later iterations.
                df_without_override_columns = df.drop(columns=override_columns)

            else:
                overrides = None
                df_without_override_columns = df

            feature_functions_df = self._compute_feature_functions(
                df_without_override_columns, functions_to_apply, overrides
            )
            return pd.concat(
                [df_without_override_columns, feature_functions_df], axis=1
            )
        return df

    # basic predict just returning predict
    def predict(self, df: pd.DataFrame, params: Optional[Dict[str, Any]] = None):
        return self._predict(df, params)

    # new method to return tuple of prediction and metrics if available
    def predict_with_metrics(
        self, df: pd.DataFrame, params: Optional[Dict[str, Any]] = None
    ):
        # if enabled, use metrics class to record metric values in child function calls
        output_metrics = None
        if self._is_lookup_client_instrumentation_enabled():
            output_metrics = LookupClientMetrics({})
        prediction = self._predict(df, params, output_metrics)
        # will add any captured metrics to output via pandas series attributes
        if output_metrics:
            return (prediction, output_metrics.get_metrics())
        else:
            return (prediction, None)

    # Dispatch to the correct predict method based on conditions.
    @trace_latency("databricks_feature_store")
    def _predict(
        self,
        df: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None,
        output_metrics=None,
    ) -> Union[Dict[str, Any], pd.DataFrame]:
        if self._is_lookup_performance_debug_enabled():
            self._latency_debugger.init()

        result = {}
        if self.eligible_for_pgsql_connection:
            if os.getenv(ENV_SERVABLE_TYPE) == "FEATURES":
                # Feature Serving: return the feature values directly as a Dict.
                result = self.pg_sql_fetcher.lookup_features(df)
                self._latency_debugger.add_latency("pg_lookup_features")
            else:
                # Model Serving: fetch the feature values in DataFrame and run the model prediction.
                model_input_df = self.pg_sql_fetcher.get_model_input_df(df)
                self._latency_debugger.add_latency("pg_get_model_input_df")
                result = self._raw_model_predict(model_input_df, params)
                self._latency_debugger.add_latency("model_predict")
        else:
            result = self._legacy_predict(df, params, output_metrics)
        latency_debug_string = self._latency_debugger.debug_string()
        if latency_debug_string:
            _logger.info(latency_debug_string)
        return result

    @trace_latency("databricks_feature_store")
    def _legacy_predict(
        self,
        df: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None,
        output_metrics=None,
    ):
        """
        This is the legacy predict method that has all functionalities supported.
        """
        (
            fully_overridden_feature_output_names,
            partially_overridden_feature_output_names,
        ) = self._get_overridden_feature_output_names(df)
        fully_overridden_feature_output_names_set = set(
            fully_overridden_feature_output_names
        )

        self._validate_input(
            df,
            fully_overridden_feature_output_names,
            partially_overridden_feature_output_names,
        )
        self._latency_debugger.add_latency("validation")

        if output_metrics and len(fully_overridden_feature_output_names) > 0:
            output_metrics.increase_metric(
                OVERRIDEN_FEATURE_COUNT,
                df[fully_overridden_feature_output_names].count().sum(),
            )
        self._latency_debugger.add_latency("m_override_ft_ctn")

        execution_groups = get_feature_execution_groups(self.feature_spec, df.columns)
        result_df = df
        self._latency_debugger.add_latency("load_groups")
        for execution_group in execution_groups:
            if execution_group.type == COLUMN_INFO_TYPE_SOURCE:
                self._latency_debugger.add_latency("eg_source")
                continue
            elif execution_group.type == COLUMN_INFO_TYPE_FEATURE:
                # Filter out fully overridden feature names, so they are not looked up unnecessarily
                result_df = self._monitored_augment_with_materialized_features(
                    result_df,
                    [
                        feature
                        for feature in execution_group.features
                        if feature.output_name
                        not in fully_overridden_feature_output_names_set
                    ],
                    partially_overridden_feature_output_names,
                    output_metrics=output_metrics,
                )
                self._latency_debugger.add_latency("eg_lookup")
            elif execution_group.type == COLUMN_INFO_TYPE_ON_DEMAND:
                result_df = self._augment_with_on_demand_features(
                    result_df, execution_group.features
                )
                self._latency_debugger.add_latency("eg_func")
            else:
                # This should never be visible to user.
                raise Exception(
                    "Unknown feature execution group type:", execution_group.type
                )
        self._latency_debugger.add_latency("execution_group_done")

        output_cols = [
            ci.output_name for ci in self.feature_spec.column_infos if ci.include
        ]
        model_input_df = result_df[output_cols]
        self._latency_debugger.add_latency("reorder_results")

        # Feature Trace logging
        # TODO: ML-49161 implement size limit for feature trace logging if needed
        if is_feature_tracing_enabled():
            with mlflow.start_span("custom_model", SpanType.RETRIEVER) as span:
                span.set_inputs(
                    {"model_input": model_input_df.to_dict(orient="records")}
                )
                prediction = self._raw_model_predict(model_input_df, params)
        else:
            prediction = self._raw_model_predict(model_input_df, params)

        self._latency_debugger.add_latency("predict")
        return prediction

    def _raw_model_predict(
        self,
        model_input_df: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None,
    ):
        if inspect.signature(self.raw_model.predict).parameters.get("params"):
            # Avoid passing result_type as params if it has the default value.
            # We are almost certain this isn't what the raw model expects.
            if (
                params
                and params.get("result_type", _NO_RESULT_TYPE_PASSED)
                == _NO_RESULT_TYPE_PASSED
            ):
                params.pop("result_type", None)
            prediction = self.raw_model.predict(model_input_df, params=params)
        else:
            prediction = self.raw_model.predict(model_input_df)
            if params:
                _logger.warning(
                    "The model does not support passing additional "
                    "parameters to the predict function. Supplied parameters "
                    "will be ignored."
                )
        return prediction

    def _get_ft_metadata(
        self,
        feature_spec: FeatureSpec,
        fts_for_serving: FeatureTablesForServing,
    ) -> Dict[str, FeatureTableMetadata]:
        ft_to_lookup_key_to_feature_col_infos = (
            self._group_fcis_by_feature_table_lookup_key(feature_spec)
        )
        ft_names = ft_to_lookup_key_to_feature_col_infos.keys()
        ft_to_online_ft = self._resolve_online_stores(
            feature_tables=ft_names, feature_tables_for_serving=fts_for_serving
        )

        return {
            ft: FeatureTableMetadata(
                feature_col_infos_by_lookup_key=ft_to_lookup_key_to_feature_col_infos[
                    ft
                ],
                online_ft=ft_to_online_ft[ft],
            )
            for ft in ft_names
        }

    @staticmethod
    def _group_fcis_by_feature_table_lookup_key(
        feature_spec: FeatureSpec,
    ) -> Dict[str, Dict[LookupKeyType, List[FeatureColumnInfo]]]:
        """
        Re-organizes the provided FeatureSpec into a convenient structure for creating
        FeatureTableMetadata objects.

        :return: Nested dictionary:
            {feature_table_name -> {lookup_key -> feature_column_infos}}
        """
        feature_table_to_lookup_key_to_fcis = defaultdict(lambda: defaultdict(list))
        for fci in feature_spec.feature_column_infos:
            feature_table_name = fci.table_name
            lookup_key = tuple(fci.lookup_key)
            feature_table_to_lookup_key_to_fcis[feature_table_name][lookup_key].append(
                fci
            )
        return feature_table_to_lookup_key_to_fcis

    def _get_overridden_feature_output_names(self, df: pd.DataFrame):
        """A feature value can be overridden in the provided DataFrame. There are two cases:
          1. The feature value is overridden for all rows in the df.
          2. The feature value is overridden for some but not all rows in the df.

        :return: Tuple<List[str], List[str]>
          (List of feature names with values that were fully overridden,
          list of feature names with values that were partially overridden)
        """
        df_columns_set = set(df.columns)
        overridden_feature_names = [
            fci.output_name
            for fci in self.feature_spec.feature_column_infos
            if fci.output_name in df_columns_set
        ]
        if len(overridden_feature_names) == 0:
            return [], []

        all_rows_overridden_idxs = df[overridden_feature_names].notna().all().values
        fully_overridden = [
            overridden_feature_names[i]
            for i in range(len(overridden_feature_names))
            if all_rows_overridden_idxs[i]
        ]
        fully_overridden_set = set(fully_overridden)
        partially_overridden = [
            name
            for name in overridden_feature_names
            if name not in fully_overridden_set
        ]
        return (fully_overridden, partially_overridden)

    def _eligible_for_pgsql_connection(self):
        if os.getenv(FEATURE_SERVING_HP) == "false":
            return False
        online_stores = [
            ft_metadata.online_ft.online_store
            for ft_metadata in self.ft_metadata.values()
        ]
        # note: it's redundant to check the length of online_stores. But adding this for clarity.
        if len(online_stores) > 0 and not all(
            online_store.store_type is StoreType.DATABRICKS_ONLINE_STORE
            for online_store in online_stores
        ):
            _logger.info(
                "Not eligible for pgsql connection because feature tables are not published to Databricks Online Store."
            )
            return False
        if (
            len(set(online_store.extra_configs.host for online_store in online_stores))
            > 1
        ):
            _logger.info(
                "Not eligible for pgsql connection because feature tables are published to different online stores."
            )
            return False
        return True

    def _validate_input(
        self,
        df: pd.DataFrame,
        fully_overridden_feature_output_names: List[str],
        partially_overridden_feature_output_names: List[str],
    ):
        """
        Validates:
            - df contains exactly one column per SourceDataColumnInfo
            - df contains exactly one column per lookup key and per function input that are not
                provided by intermediate lookups or functions
            - df has no NaN lookup keys
        """
        req_source_column_names = [
            col_info.name for col_info in self.feature_spec.source_data_column_infos
        ]
        lookup_key_columns = set(
            itertools.chain.from_iterable(
                [
                    col_info.lookup_key
                    for col_info in self.feature_spec.feature_column_infos
                ]
            )
        )
        function_input_binding_columns = set(
            itertools.chain.from_iterable(
                [
                    col_info.input_bindings.values()
                    for col_info in self.feature_spec.on_demand_column_infos
                ]
            )
        )

        lookup_output_columns = set(
            [ci.output_name for ci in self.feature_spec.feature_column_infos]
        )
        function_output_columns = set(
            [ci.output_name for ci in self.feature_spec.on_demand_column_infos]
        )

        # All input and output excluding source columns.
        all_input_columns = function_input_binding_columns.union(lookup_key_columns)
        all_output_columns = lookup_output_columns.union(function_output_columns)

        all_req_columns = set(req_source_column_names).union(
            all_input_columns.difference(all_output_columns)
        )
        df_column_set = set(df.columns)
        missing_columns = [c for c in all_req_columns if c not in df_column_set]

        if missing_columns:
            raise ValueError(
                f"Input is missing columns {list(missing_columns)}. "
                f"\n\tThe following columns are required: {list(all_req_columns)}."
            )

        df_column_name_counts = Counter(df.columns)
        no_dup_columns_allowed_set = set(
            list(lookup_key_columns)
            + req_source_column_names
            + fully_overridden_feature_output_names
            + partially_overridden_feature_output_names
        )
        dup_columns = [
            col
            for col, count in df_column_name_counts.items()
            if count > 1 and col in no_dup_columns_allowed_set
        ]

        if dup_columns:
            raise ValueError(
                f"Input has duplicate columns: {dup_columns}"
                f"\n\tThe following column names must be unique: {no_dup_columns_allowed_set}"
            )

        # The set of columns from the input that are required as lookup keys.
        # This set doesn't include lookup keys that can be provided by intermediate lookup or
        # function result.
        lookup_key_columns_from_input = lookup_key_columns.difference(
            all_output_columns
        )
        lookup_key_df = df[list(lookup_key_columns_from_input)]
        cols_with_nulls = lookup_key_df.columns[lookup_key_df.isnull().any()].tolist()
        if cols_with_nulls:
            raise ValueError(
                f"Failed to lookup feature values due to null values for lookup_key columns "
                f"{cols_with_nulls}. The following columns cannot contain null values: "
                f"{lookup_key_columns}"
            )

    @timeout(seconds=TOTAL_REQUEST_TIMEOUT_SECONDS)
    def _augment_with_materialized_features(
        self,
        df: pd.DataFrame,
        features_to_lookup: List[FeatureColumnInfo],
        partially_overridden_feature_output_names: List[str],
        *,
        metrics: LookupClientMetrics = None,
    ) -> pd.DataFrame:
        """
        Adds materialized features to `df`. This function does not filter out ColumnInfos with
        include=False, however it will drop any columns in `df` that are not in the FeatureSpec.
        features_to_lookup MUST NOT include any fully overridden features already in df; however,
        partially overridden features are allowed and non-overridden cells will be looked up.

        For example, a FeatureSpec may include

            - revenue:
                include: false
                source: training_data
            - cost:
                include: false
                source: training_data
            - profit:
                udf_name: prod.math.subtract
                input_bindings:
                  x: sales
                  y: cost
                source: on_demand_feature

         In this case, the DataFrame returned by this method will include columns `revenue` and
         `cost`. This is required to compute the Feature Function `profit` at a later stage.

        :param df: Pandas DataFrame provided by user as model input. This is expected to contain
        columns for each SourceColumnInfo, and for each lookup key of a FeatureColumnInfo. Columns
        with the same name as FeatureColumnInfo output_names will override those features, meaning
        they will not be queried from the online store.
        :param features_to_lookup: List of FeatureColumnInfos to lookup from the online store.
        :param partially_overridden_feature_output_names: List of feature output names that are
        partially overridden in `df`. These features will be looked up from the online store, and
        only the cells that are not overridden will be looked up.
        :return: Pandas DataFrame containing all materialized features specified in the FeatureSpec,
          including features with include=False (see example above).
        """
        # Contains lookup result columns. Does not include fully overridden columns.
        feature_dfs = []
        partially_overridden_features_count = 0
        partially_overridden_feature_output_names_set = set(
            partially_overridden_feature_output_names
        )

        pk_lists = defaultdict(lambda: defaultdict(list))
        feature_column_infos_to_lookup_dict = defaultdict(lambda: defaultdict(list))
        lookup_clients = {}

        table_names_to_lookup = {info.table_name for info in features_to_lookup}
        all_lookup_columns = {info.output_name for info in features_to_lookup}

        # Query online store(s) for feature values
        ft_meta: FeatureTableMetadata
        for ft_name, ft_meta in self.ft_metadata.items():
            if ft_name not in table_names_to_lookup:
                continue
            if not self.is_model_eligible_for_batch_lookup:
                lookup_clients[
                    ft_meta.online_ft.online_feature_table_name
                ] = self.ft_to_lookup_client[ft_name]

            # Iterate through the lookup_keys for this feature table, each of which is used to
            # lookup a list of features
            lookup_key: LookupKeyType
            feature_column_infos: List[FeatureColumnInfo]
            for (
                lookup_key,
                feature_column_infos,
            ) in ft_meta.feature_col_infos_by_lookup_key.items():
                # Only lookup features that were specified in features_to_lookup
                feature_column_infos_to_lookup = [
                    fci
                    for fci in feature_column_infos
                    if fci.output_name in all_lookup_columns
                ]
                if len(feature_column_infos_to_lookup) == 0:
                    # All features were overridden in the input DataFrame
                    continue

                pk_lists[ft_meta.online_ft.online_feature_table_name][
                    lookup_key
                ] = get_primary_key_list(lookup_key, ft_meta.online_ft.primary_keys, df)
                feature_column_infos_to_lookup_dict[
                    ft_meta.online_ft.online_feature_table_name
                ][lookup_key] = feature_column_infos_to_lookup
        self._latency_debugger.add_latency("lk_prepare")

        # A nested defaultdict using table_name as first layer key and lookup_key as second layer
        # key. The actual inner value of the dict is of type pd.DataFrame. The structure looks like:
        # table_name: {
        #   lookup_key: DataFrame
        # }
        # TODO[ML-34263]: consider updating the default value type to match the actual usage.
        feature_values_dfs = defaultdict(lambda: defaultdict(list))
        if self.is_model_eligible_for_batch_lookup and pk_lists:
            feature_values_dfs = self._batch_lookup_and_rename_features(
                self.batch_lookup_client,
                pk_lists,
                feature_column_infos_to_lookup_dict,
                metrics=metrics,
            )
            self._latency_debugger.add_latency("lk_batch")
        else:
            for oft_name, pk_list_by_lookup_key in pk_lists.items():
                for lookup_key in pk_list_by_lookup_key.keys():
                    feature_values_dfs[oft_name][
                        lookup_key
                    ] = self._lookup_and_rename_features(
                        lookup_clients[oft_name],
                        pk_lists[oft_name][lookup_key],
                        feature_column_infos_to_lookup_dict[oft_name][lookup_key],
                        metrics=metrics,
                        feature_data_type_mapping=self.table_feature_data_type_mapping[
                            oft_name
                        ],
                    )
                    self._latency_debugger.add_latency("lk_table")

        for oft_name, feature_values_df_by_lookup_key in feature_values_dfs.items():
            for (
                lookup_key,
                feature_values_df,
            ) in feature_values_df_by_lookup_key.items():
                if feature_values_df.shape[0] != df.shape[0]:
                    raise Exception(
                        f"Internal Error: Expected {df.shape[0]} rows to be looked up from feature "
                        f"table {ft_name}, but found {feature_values_df.shape[0]}"
                    )

                # If any features were partially overridden, use the override values.
                # Filter all partially overridden feature output names down to those that
                # are in the feature table currently being processed.
                partially_overridden_feats = [
                    c
                    for c in feature_values_df.columns
                    if c in partially_overridden_feature_output_names_set
                ]
                if partially_overridden_feats:
                    # add partially overriden features to override count, count() returns the number
                    # of non-NaN values per column those are the values that will get overriden
                    partially_overridden_features_count += (
                        df[partially_overridden_feats].count().sum()
                    )
                    # For each cell of overridden column, use the overridden value if provided, else
                    # the value looked up from the online store.
                    partially_overridden_feats_df = df[
                        partially_overridden_feats
                    ].combine_first(feature_values_df[partially_overridden_feats])
                    feature_values_df[
                        partially_overridden_feats
                    ] = partially_overridden_feats_df[partially_overridden_feats]

                feature_dfs.append(feature_values_df)

        feature_names_looked_up = [feat for df in feature_dfs for feat in df.columns]
        used_partial_feature_names = (
            partially_overridden_feature_output_names_set.intersection(
                set(feature_names_looked_up)
            )
        )

        # Concatenate the following DataFrames, where N is the number of rows in `df`.
        #  1. feature_dfs - List of DataFrames, one per feature table looked up from the online
        #       store, containing partially overridden columns. Each DataFrame has N rows.
        #  2. non_overridden_columns_df - columns from `df` that are not partially overriden or are
        #       not looked-up in this iteration. DataFrame with N rows.
        non_overridden_columns_df = df.drop(columns=list(used_partial_feature_names))
        augmented_features = pd.concat(
            feature_dfs + [non_overridden_columns_df],
            axis=1,
        )
        self._latency_debugger.add_latency("lk_partial")

        if metrics:
            metrics.increase_metric(
                OVERRIDEN_FEATURE_COUNT, partially_overridden_features_count
            )

        return augmented_features

    def _compute_feature_functions(
        self,
        ff_inputs: pd.DataFrame,
        functions_to_apply: List[OnDemandColumnInfo],
        ff_overrides: Optional[pd.DataFrame],
    ) -> pd.DataFrame:
        """
        Executes Feature Functions specified by FeatureSpec.

        :param ff_inputs: A DataFrame containing all inputs required to evaluate Feature Functions.
          Additional columns are permitted.
        :param ff_overrides: A DataFrame containing overrides to Feature Functions. When a Feature
          Function output name is included as a column in `ff_overrides`, the function is computed
          only for rows where the override is `np.nan`.
        :return: DataFrame containing computed Feature Function columns
        """
        # TODO(ML-30619): Short-circuit Feature Function execution when overridden
        feature_function_df = self.feature_function_executor.execute_feature_functions(
            ff_inputs,
            functions_to_apply,
        )
        if ff_overrides is None:
            return feature_function_df

        ff_overrides_columns_set = set(ff_overrides.columns)
        overridden_ff_outputs = [
            odci.output_name
            for odci in functions_to_apply
            if odci.output_name in ff_overrides_columns_set
        ]
        overridden_ff_df = ff_overrides[overridden_ff_outputs]
        # As with materialized features, Feature Functions may be fully or partially
        # overridden, where a partial override means that some rows have null override value.
        # Merge the overridden values with the computed feature values:
        return overridden_ff_df.combine_first(feature_function_df)

    def _lookup_and_rename_features(
        self,
        lookup_client: OnlineLookupClient,
        primary_key_list: LookupKeyList,
        feature_column_infos: List[FeatureColumnInfo],
        *,
        metrics: LookupClientMetrics = None,
        feature_data_type_mapping: dict = None,
    ) -> pd.DataFrame:
        """
        Looks up features from a single feature table, then renames them. Feature metadata is
         specified via `feature_column_infos`.
        """
        feature_names = [fci.feature_name for fci in feature_column_infos]
        feature_values = lookup_client.lookup_features(
            primary_key_list, feature_names, metrics=metrics
        )
        feature_name_to_output_name = {
            fci.feature_name: fci.output_name for fci in feature_column_infos
        }

        feature_name_to_default_values = {}
        for fci in feature_column_infos:
            if fci.feature_name not in feature_data_type_mapping:
                _logger.warning(
                    f"_lookup_and_rename_features: Data type not found for unexpected feature {fci.feature_name}, default value will be ignored."
                )
                continue

            default_value = deserialize_default_value_to_data_type(
                fci.default_value_str, feature_data_type_mapping[fci.feature_name]
            )
            if default_value is not None:
                feature_name_to_default_values[fci.feature_name] = default_value

        if feature_name_to_default_values:
            feature_values = feature_values.fillna(value=feature_name_to_default_values)

        return feature_values.rename(feature_name_to_output_name, axis=1)

    def _batch_lookup_and_rename_features(
        self,
        batch_lookup_client: OnlineLookupClient,
        primary_key_lists: Dict[str, Dict[LookupKeyType, LookupKeyList]],
        feature_column_infos_dict: Dict[
            str, Dict[LookupKeyType, List[FeatureColumnInfo]]
        ],
        *,
        metrics: LookupClientMetrics = None,
    ) -> Dict[str, Dict[LookupKeyType, pd.DataFrame]]:
        """
        Looks up features from all the feature tables in batch, then renames them. Feature metadata
         is specified via `feature_column_infos`.
        """
        feature_names = defaultdict(lambda: defaultdict(list))
        feature_name_to_output_names = defaultdict(lambda: defaultdict(str))
        feature_name_to_default_values = defaultdict(lambda: defaultdict(lambda: None))
        for (
            oft_name,
            feature_column_infos_by_lookup_key,
        ) in feature_column_infos_dict.items():
            for (
                lookup_key,
                feature_column_infos,
            ) in feature_column_infos_by_lookup_key.items():
                feature_names[oft_name][lookup_key] = [
                    fci.feature_name for fci in feature_column_infos
                ]
                feature_name_to_output_names[oft_name][lookup_key] = {
                    fci.feature_name: fci.output_name for fci in feature_column_infos
                }

                feature_name_to_default_values[oft_name][lookup_key] = {}
                for fci in feature_column_infos:
                    if (
                        fci.feature_name
                        not in self.table_feature_data_type_mapping[oft_name]
                    ):
                        _logger.warning(
                            f"_batch_lookup_and_rename_features: Data type not found for unexpected feature {fci.feature_name}, default value will be ignored."
                        )
                        continue

                    default_value = deserialize_default_value_to_data_type(
                        fci.default_value_str,
                        self.table_feature_data_type_mapping[oft_name][
                            fci.feature_name
                        ],
                    )
                    if default_value is not None:
                        feature_name_to_default_values[oft_name][lookup_key][
                            fci.feature_name
                        ] = default_value

        feature_values = batch_lookup_client.batch_lookup_features(
            primary_key_lists, feature_names, metrics=metrics
        )

        for oft_name, feature_values_by_lookup_key in feature_values.items():
            for lookup_key, _ in feature_values_by_lookup_key.items():
                feature_values_by_oft_and_lookup_key = feature_values[oft_name][
                    lookup_key
                ]
                if feature_name_to_default_values[oft_name][lookup_key]:
                    feature_values_by_oft_and_lookup_key = (
                        feature_values_by_oft_and_lookup_key.fillna(
                            value=feature_name_to_default_values[oft_name][lookup_key]
                        )
                    )
                feature_values[oft_name][
                    lookup_key
                ] = feature_values_by_oft_and_lookup_key.rename(
                    feature_name_to_output_names[oft_name][lookup_key], axis=1
                )
        return feature_values

    def _resolve_online_stores(
        self,
        feature_tables: List[str],
        feature_tables_for_serving: FeatureTablesForServing,
    ) -> Dict[str, OnlineFeatureTable]:
        """
        :return: feature table name -> OnlineFeatureTable
        """
        all_fts_to_online_ft = {
            online_ft.feature_table_name: online_ft
            for online_ft in feature_tables_for_serving.online_feature_tables
        }

        missing = [ft for ft in feature_tables if ft not in all_fts_to_online_ft]
        if missing:
            raise Exception(
                f"Internal error: Online feature table information could not be found "
                f"for feature tables {missing}."
            )

        return {ft: all_fts_to_online_ft[ft] for ft in feature_tables}


def _load_pyfunc(path):
    """
    Called by ``pyfunc.load_pyfunc``.
    """
    return _FeatureStoreModelWrapper(path)
