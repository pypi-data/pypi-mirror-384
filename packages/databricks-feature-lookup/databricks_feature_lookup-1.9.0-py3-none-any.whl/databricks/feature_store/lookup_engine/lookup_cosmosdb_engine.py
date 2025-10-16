"""
Defines the LookupCosmosDbEngine class, which is used to perform lookups on Cosmos DB online stores.
"""

import functools
import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from azure.cosmos import CosmosClient

from databricks.feature_store.lookup_engine.lookup_engine import LookupEngine
from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.feature_store.utils.cosmosdb_type_utils import (
    COSMOSDB_DATA_TYPE_CONVERTER_FACTORY,
)
from databricks.feature_store.utils.cosmosdb_utils import (
    DEFAULT_RETRY_CONFIG,
    FEATURE_STORE_SENTINEL_ID_VALUE,
    PARTITION_KEY,
    PATHS,
    PRIMARY_KEY_PROPERTY_NAME_VALUE,
    is_not_found_error,
    to_cosmosdb_primary_key,
)
from databricks.feature_store.utils.metrics_utils import (
    NAN_FEATURE_COUNT,
    LookupClientMetrics,
    lookup_call_maybe_with_metrics,
    num_missing_feature_values,
)
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
)
from databricks.ml_features_common.entities.query_mode import QueryMode

_logger = logging.getLogger(__name__)

LookupKeyType = Tuple[str, ...]


class LookupCosmosDbEngine(LookupEngine):
    def __init__(
        self, online_feature_table: OnlineFeatureTable, authorization_key: str
    ):
        """
        :param online_feature_table: OnlineFeatureTable to look up feature values from.
        :param authorization_key: Uses this authorization key to authenticate with Cosmos DB.
        """
        # The online feature table name is 2L for HMS tables and either 2L or 3L for UC tables.
        # 2L name "database.table" is mapped to Cosmos DB database="database", container="table".
        # 3L name "catalog.schema.table" is mapped to Cosmos DB database="catalog.schema", container="table".
        self.online_table_name = online_feature_table.online_feature_table_name
        self.database_name, self.container_name = self.online_table_name.rsplit(".", 1)

        # Retrieve the relevant configuration and helpers needed for lookup.
        self.account_uri = online_feature_table.online_store.extra_configs.account_uri
        self.query_mode = online_feature_table.online_store.query_mode
        self.timestamp_keys = online_feature_table.timestamp_keys
        self.primary_keys_to_type_converter = {
            pk.name: COSMOSDB_DATA_TYPE_CONVERTER_FACTORY.get_converter(pk)
            for pk in online_feature_table.primary_keys
        }
        self.features_to_type_converter = {
            feature.name: COSMOSDB_DATA_TYPE_CONVERTER_FACTORY.get_converter(feature)
            for feature in online_feature_table.features
        }

        # Initialize the CosmosClient used for lookup.
        self._client = CosmosClient(
            self.account_uri, authorization_key, **DEFAULT_RETRY_CONFIG
        )
        self._database_client = self._client.get_database_client(self.database_name)
        self._container_client = self._database_client.get_container_client(
            self.container_name
        )
        self._validate_online_feature_table()

    def _validate_online_feature_table(
        self,
    ) -> None:
        # Check that the online container exists and retrieve its details.
        # Otherwise, a CosmosResourceNotFoundError exception is thrown.
        container_desc = self._container_client.read()

        # All container descriptions contain the partition key and paths. Check the partition key is as expected.
        partition_key_paths = container_desc[PARTITION_KEY][PATHS]
        if partition_key_paths != [f"/{PRIMARY_KEY_PROPERTY_NAME_VALUE}"]:
            raise ValueError(
                f"Online Table {self.online_table_name} primary key schema is not configured properly."
            )

    def lookup_features(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
        *,
        metrics: LookupClientMetrics = None,
    ) -> pd.DataFrame:
        query = functools.partial(
            self._run_lookup_cosmosdb_query, feature_names, metrics=metrics
        )
        results = [query(row) for row in lookup_list.items]
        feature_df = pd.DataFrame(results, columns=feature_names)
        return feature_df

    def batch_lookup_features(
        self,
        lookup_list_dict: Dict[str, Dict[LookupKeyType, LookupKeyList]],
        feature_names_dict: Dict[str, Dict[LookupKeyType, List[str]]],
        *,
        metrics: LookupClientMetrics = None,
    ) -> Dict[str, Dict[LookupKeyType, pd.DataFrame]]:
        raise NotImplementedError

    def _lookup_primary_key(self, cosmosdb_primary_key: str):
        try:
            # The expected response is the item with additional system properties, e.g. {"feat1": ..., "sys1": ...}
            # It's not possible to selectively retrieve features when using point reads (`client.read_item`).
            # However, point reads are recommended over queries (`client.query_items`) for performance and cost.
            # https://docs.microsoft.com/en-us/azure/cosmos-db/optimize-cost-reads-writes

            # As of azure-cosmos==4.2.0 (the minimum required version), `client.read_item` retries up to either of:
            # 30 seconds of timeout or 9 total attempts. Thus, no manual retry handling needs to be done.
            return self._container_client.read_item(
                item=FEATURE_STORE_SENTINEL_ID_VALUE, partition_key=cosmosdb_primary_key
            )
        except Exception as e:
            # Return None if the error was caused by read_item finding no result. Otherwise,
            # re-raise the error.
            # The existence of the CosmosDB container is validated during __init__, so any NotFound
            # is caused by a missing item.
            if is_not_found_error(e):
                return None
            _logger.warning(
                f"Encountered error reading from {self.online_table_name}:\n{e}"
            )
            raise e

    def _run_lookup_cosmosdb_query(
        self,
        feature_names: List[str],
        lookup_row: List[Tuple[str, Any]],
        *,
        metrics: LookupClientMetrics = None,
    ):
        """
        This helper function executes a single Cosmos DB query.
        """
        cosmosdb_lookup_row = self._pandas_to_cosmosdb(lookup_row)
        cosmosdb_primary_key = to_cosmosdb_primary_key(cosmosdb_lookup_row)
        if self.query_mode == QueryMode.PRIMARY_KEY_LOOKUP:
            lookup_pk = lookup_call_maybe_with_metrics(
                self._lookup_primary_key, metrics
            )
            feature_values = lookup_pk(cosmosdb_primary_key)
        else:
            raise ValueError(f"Unsupported query mode: {self.query_mode}")

        if not feature_values:
            _logger.warning(
                f"No feature values found in {self.online_table_name} for {cosmosdb_lookup_row}."
            )
            nan_features_count = len(feature_names)
            if metrics:
                metrics.increase_metric(NAN_FEATURE_COUNT, nan_features_count)
            return np.full(len(feature_names), np.nan)

        results = [feature_values.get(f, np.nan) for f in feature_names]
        nan_features_count = num_missing_feature_values(feature_names, feature_values)

        if metrics:
            # 0 nan feature count still needs to be recorded to propagate metrics for inference request
            metrics.increase_metric(NAN_FEATURE_COUNT, nan_features_count)

        # Return the result
        return self._cosmosdb_to_pandas(results, feature_names)

    def _pandas_to_cosmosdb(self, row: List[Tuple[str, Any]]) -> List[Any]:
        """
        Converts the input Pandas row to the Cosmos DB online equivalent Python types.
        """
        return [
            self.primary_keys_to_type_converter[pk_name].to_online_store(pk_value)
            for pk_name, pk_value in row
        ]

    def _cosmosdb_to_pandas(
        self, results: List[Any], feature_names: List[str]
    ) -> List[Any]:
        """
        Converts the online store retrieved item to Pandas compatible Python values for the given features.
        """
        feature_names_and_values = zip(feature_names, results)
        return [
            self.features_to_type_converter[feature_name].to_pandas(feature_value)
            for feature_name, feature_value in feature_names_and_values
        ]

    def shutdown(self) -> None:
        """
        Cleans up the store connection if it exists on the Cosmos DB online store.
        :return:
        """
        # Cosmos DB connections are stateless http connections and hence do not need an explicit
        # shutdown operation.
        pass
