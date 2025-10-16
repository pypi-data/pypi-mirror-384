""" Defines the LookupSqlEngine class, which is used to perform
lookups on SQL databases. This class differs from PublishSqlEngine in that
its actions are read-only, and uses a Python connector instead of Java.
"""

import abc
import functools
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import sqlalchemy

from databricks.feature_store.lookup_engine.lookup_engine import LookupEngine
from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.feature_store.utils.logging_utils import get_logger
from databricks.feature_store.utils.metrics_utils import (
    NAN_FEATURE_COUNT,
    LookupClientMetrics,
    lookup_call_maybe_with_metrics,
)
from databricks.feature_store.utils.sql_type_utils import (
    SQL_DATA_TYPE_CONVERTER_FACTORY,
)
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
)

_logger = get_logger(__name__, log_level=logging.INFO)

LookupKeyType = Tuple[str, ...]


class LookupSqlEngine(LookupEngine):
    INFORMATION_SCHEMA = "INFORMATION_SCHEMA"
    TABLES = "TABLES"
    TABLE_CATALOG = "TABLE_CATALOG"
    TABLE_SCHEMA = "TABLE_SCHEMA"
    TABLE_NAME = "TABLE_NAME"
    COLUMNS = "COLUMNS"
    COLUMN_NAME = "COLUMN_NAME"
    COLUMN_KEY = "COLUMN_KEY"
    DATA_TYPE = "DATA_TYPE"
    TABLE_CONSTRAINTS = "TABLE_CONSTRAINTS"
    CONSTRAINT_COLUMN_USAGE = "CONSTRAINT_COLUMN_USAGE"
    CONSTRAINT_TYPE = "CONSTRAINT_TYPE"
    CONSTRAINT_NAME = "CONSTRAINT_NAME"

    @abc.abstractmethod
    def __init__(
        self, online_feature_table: OnlineFeatureTable, ro_user: str, ro_password: str
    ):
        self.online_store = online_feature_table.online_store

        result = self._get_database_and_table_name(
            online_feature_table.online_feature_table_name
        )
        (self.database_name, self.schema_name, self.table_name) = result

        self.user = ro_user
        self.password = ro_password
        self.host = self.online_store.extra_configs.host
        self.port = self.online_store.extra_configs.port

        self.primary_keys = online_feature_table.primary_keys
        self.feature_names_to_feature_details = {
            f.name: f for f in online_feature_table.features
        }
        self.features_to_type_converter = {
            feature.name: SQL_DATA_TYPE_CONVERTER_FACTORY.get_converter(feature)
            for feature in online_feature_table.features
        }
        # caching the query
        self.previous_key_columns = None
        self.previous_feature_columns = None
        self.previous_query = None

        if not self.is_lakebase_engine():
            # A validation is not really necessary. But keep it for legacy implementations
            # to make the behavior unchanged.
            self._validate_online_feature_table()

    def _get_database_and_table_name(
        self, online_table_name
    ) -> Tuple[str, Optional[str], str]:
        raise NotImplementedError

    @contextmanager
    def _get_connection(self):
        # Everything between here and the yield statement will be executed in contextmanager.__enter__()

        # We create a SQL engine instance per required online table in an inference request and dispose it afterwards.
        # A single inference request runs queries sequentially, so a connection pool is not required or beneficial.
        # TODO (ML-23188): Investigate sharing a long lived SQL engine and connection pool across inference requests.
        engine = sqlalchemy.create_engine(
            self.engine_url, poolclass=sqlalchemy.pool.NullPool
        )
        connection = engine.connect()

        # When the caller invokes "with _get_connection() as x", the connection will be returned as "x"
        yield connection

        # Everything below here will be executed in contextmanager.__exit__()

        connection.close()
        # Disposing the engine prevents connections from hanging around in memory if a connection pool is used.
        engine.dispose()

    @property
    def engine_url(self) -> str:
        raise NotImplementedError

    # Base implementation that runs a single row query for each lookup row.
    # Lakebase engine overrides this method and bulk fetches features for multiple rows.
    def _get_sql_results(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
        metrics: LookupClientMetrics = None,
    ) -> List[sqlalchemy.engine.Row]:
        if (
            self.previous_key_columns == lookup_list.columns
            and self.previous_feature_columns == feature_names
        ):
            query = self.previous_query
        else:
            pk_filter_phrase = " AND ".join(
                [f"{self._sql_safe_name(pk)} = :{pk}" for pk in lookup_list.columns]
            )
            select_feat_phrase = ", ".join(
                f"{self._sql_safe_name(f)}" for f in feature_names
            )

            safe_table_name = self._sql_safe_name(self.table_name)
            table_name_phrase = (
                f"{self._sql_safe_name(self.schema_name)}.{safe_table_name}"
                if self.schema_name
                else safe_table_name
            )

            query = sqlalchemy.sql.text(
                f"SELECT {select_feat_phrase} FROM {table_name_phrase} WHERE {pk_filter_phrase}"
            )
            self.previous_key_columns = lookup_list.columns
            self.previous_feature_columns = feature_names
            self.previous_query = query

        with self._get_connection() as sql_connection:
            run_query = functools.partial(
                self._run_lookup_sql_query,
                sql_connection,
                query,
                feature_names,
                metrics,
            )
            return [run_query(row) for row in lookup_list.items]

    # To be overridden by subclasses
    def is_lakebase_engine(self) -> bool:
        return False

    def lookup_features(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
        *,
        metrics: LookupClientMetrics = None,
    ) -> pd.DataFrame:
        """
        Lookups features from one table. Returns the results in format of a pandas DataFrame
        and cast the values to the exact data type as specified by FeatureLookup and FeatureFunctions.
        """
        results = self._get_sql_results(lookup_list, feature_names, metrics=metrics)

        feature_df = pd.DataFrame(results, columns=feature_names)

        feature_df.columns = feature_names
        for feature in feature_names:
            feature_df[feature] = feature_df[feature].map(
                lambda x: (
                    self.features_to_type_converter[feature].to_pandas(x) if x else x
                ),
                na_action="ignore",
            )
        return feature_df

    def lookup_feature_dicts(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Lookups features from one table. Returns the results in format of a List of Dict
        whose keys are the column names and values are the feature values.
        """
        results = self._get_sql_results(lookup_list, feature_names)
        # results cannot be empty.
        if isinstance(results[0], np.ndarray):
            # handle not found case
            return [{name: None for name in feature_names}]
        elif isinstance(results[0], dict):
            # handle case where results are already dictionaries (e.g., from lakebase engine)
            return results
        else:
            return [row._asdict() for row in results]

    def batch_lookup_features(
        self,
        lookup_list_dict: Dict[str, Dict[LookupKeyType, LookupKeyList]],
        feature_names_dict: Dict[str, Dict[LookupKeyType, List[str]]],
        *,
        metrics: LookupClientMetrics = None,
    ) -> Dict[str, Dict[LookupKeyType, pd.DataFrame]]:
        raise NotImplementedError

    def _validate_online_feature_table(
        self,
    ) -> None:
        # Validate the Python database connection specified by the database location in OnlineFeatureTable.
        # Throw operational error if new connection is invalid
        try:
            with self._get_connection() as sql_connection:
                # Validate the online feature table exists in online database as specified by the OnlineFeatureTable.
                if not self._database_contains_feature_table(sql_connection):
                    raise ValueError(
                        f"Table {self.table_name} does not exist in database {self.database_name}."
                    )

                    # Validate the online feature table has the same primary keys specified by the OnlineFeatureTable.
                if not self._database_contains_primary_keys(sql_connection):
                    raise ValueError(
                        f"Table {self.table_name} does not contain primary keys {self.primary_keys}."
                    )
        except Exception as e:
            raise ValueError(f"Connection could not be established: {str(e)}.")

    def shutdown(self) -> None:
        """
        Closes the database connection if it exists on the SQL lookup engine.
        :return:
        """
        self._close()

    def _close(self) -> None:
        """
        This is a no-op because a new sql connection is opened for each query and closed after the query executes.
        """
        pass

    def _run_lookup_sql_query(
        self,
        sql_connection,
        query,
        feature_names,
        metrics,
        lookup_row: List[Tuple[str, Any]],
    ):
        """
        This helper function executes a single SQL query .
        """
        query_params = dict(lookup_row)
        run_lookup = lookup_call_maybe_with_metrics(sql_connection.execute, metrics)
        sql_data = run_lookup(query, query_params)
        feat_values = sql_data.fetchall()
        if len(feat_values) == 0:
            _logger.warning(
                f"No feature values found in {self.table_name} for {query_params}."
            )
            nan_features = np.empty(len(feature_names))
            nan_features[:] = np.nan
            if metrics:
                # 0 nan feature count still needs to be recorded to propogate metrics for inference request
                metrics.increase_metric(NAN_FEATURE_COUNT, len(nan_features))

            return nan_features
        # Return the first result
        return feat_values[0]

    @classmethod
    def _sql_safe_name(cls, name):
        raise NotImplementedError

    def _database_contains_feature_table(self, sql_connection):
        raise NotImplementedError

    def _database_contains_primary_keys(self, sql_connection):
        raise NotImplementedError
