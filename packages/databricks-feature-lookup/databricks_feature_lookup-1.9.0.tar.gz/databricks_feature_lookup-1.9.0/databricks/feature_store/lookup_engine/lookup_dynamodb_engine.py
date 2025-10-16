""" Defines the LookupDynamoDbEngine class, which is used to perform lookups on DynamoDB store.
"""

import functools
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from databricks.feature_store.lookup_engine.lookup_engine import LookupEngine
from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.feature_store.utils.dynamodb_type_utils import (
    DYNAMODB_DATA_TYPE_CONVERTER_FACTORY,
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
from databricks.ml_features_common.utils.dynamodb_utils import (
    ATTRIBUTES_TO_GET,
    BATCH_GET_ITEM_LIMIT,
    ITEM,
    ITEMS,
    KEY_SCHEMA,
    KEYS,
    PRIMARY_KEY_ATTRIBUTE_NAME_VALUE,
    PRIMARY_KEY_SCHEMA,
    TABLE,
    get_dynamodb_resource,
    key_schemas_equal,
    merge_batched_results,
    paginate_keys,
    to_dynamodb_primary_key,
    to_range_schema,
    to_safe_select_expression,
)

_logger = logging.getLogger(__name__)
LookupKeyType = Tuple[str, ...]


def as_list(obj, default=None):
    if not obj:
        return default
    elif isinstance(obj, list):
        return obj
    else:
        return [obj]


LookupKeyType = Tuple[str, ...]


class AwsAccessKey:
    def __init__(self, access_key_id: str, secret_access_key: str):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key


class LookupDynamoDbEngine(LookupEngine):
    def __init__(
        self,
        online_feature_table: Union[OnlineFeatureTable, List[OnlineFeatureTable]],
        access_key: Optional[AwsAccessKey],
    ):
        """
        :param online_feature_table: OnlineFeatureTable to look up feature values from. If
            a list of online feature tables is passed, they should have the same access credentials.
        :param access_key: Uses this access key to authenticate with AWS, if provided. If None,
        role-based authentication is used.
        """
        online_feature_table_as_list = as_list(online_feature_table)
        self._online_feature_table_names_list = [
            oft.online_feature_table_name for oft in online_feature_table_as_list
        ]
        self._query_mode_map = {
            oft.online_feature_table_name: oft.online_store.query_mode
            for oft in online_feature_table_as_list
        }
        self._timestamp_keys_map = {
            oft.online_feature_table_name: oft.timestamp_keys
            for oft in online_feature_table_as_list
        }
        # All online feature tables should have the same region, so we only query for the first one.
        self._region = online_feature_table_as_list[0].online_store.extra_configs.region

        self._primary_keys_to_type_converter_map = {
            oft.online_feature_table_name: {
                pk.name: DYNAMODB_DATA_TYPE_CONVERTER_FACTORY.get_converter(pk)
                for pk in oft.primary_keys
            }
            for oft in online_feature_table_as_list
        }
        self._features_to_type_converter_map = {
            oft.online_feature_table_name: {
                feature.name: DYNAMODB_DATA_TYPE_CONVERTER_FACTORY.get_converter(
                    feature
                )
                for feature in oft.features
            }
            for oft in online_feature_table_as_list
        }

        self._dynamodb_resource = get_dynamodb_resource(
            access_key_id=access_key.access_key_id if access_key else None,
            secret_access_key=access_key.secret_access_key if access_key else None,
            region=self._region,
        )
        self._dynamodb_client = self._dynamodb_resource.meta.client
        self._validate_online_feature_table()

    def lookup_features(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
        *,
        metrics: LookupClientMetrics = None,
    ) -> pd.DataFrame:
        # Serial lookup on the only online feature table.
        if len(self._online_feature_table_names_list) > 1:
            raise ValueError(f"Batch engine should not use serial lookup.")
        query = functools.partial(
            self._run_lookup_dynamodb_query,
            feature_names,
            self._online_feature_table_names_list[0],
            metrics=metrics,
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
        """
        :param lookup_list_dict: dictionary from online feature table name to a dictionary from
            lookup key to primary key table.
        :param feature_names_dict:  dictionary from online feature table name to feature names.
        :return Dictionary from online feature table name to a dictionary from lookup key to feature values dataframe.
        """

        # A dictionary that maps online feature table name to a list of primary key records
        batch_keys = {}
        # A dictionary that maps online feature table name to a list of features to retrieve
        attribute_map = {}
        # A dictionary that maps online feature table name to a dictionary of lookup key to
        # a list of primary keys.
        primary_key_dict = {}
        for table in self._online_feature_table_names_list:
            if table not in lookup_list_dict:
                # skip the tables that are not in this batch.
                continue
            primary_key_lists = []
            primary_key_dict[table] = {}
            feature_names_set = set()
            feature_names = []
            for lookup_key, lookup_list in lookup_list_dict[table].items():
                current_feature_names = feature_names_dict[table][lookup_key]
                # (TODO: ML-26588): Performance profiling.
                for feature in current_feature_names:
                    if feature not in feature_names_set:
                        feature_names_set.add(feature)
                        feature_names.append(feature)

                # Convert the lookup keys to primary keys in the online feature table.
                function = functools.partial(
                    self._pandas_to_dynamodb_primary_keys, table
                )
                primary_key_list = [function(row) for row in lookup_list.items]
                primary_key_dict[table][lookup_key] = primary_key_list
                primary_key_lists.append(primary_key_list)

            # The explicit looping is intentional to keep the deterministic ordering of lookup keys
            # for stability and predictability.
            concatenated_primary_keys_set = set()
            concatenated_primary_keys = []
            for primary_key_list in primary_key_lists:
                for primary_key in primary_key_list:
                    if primary_key not in concatenated_primary_keys_set:
                        concatenated_primary_keys_set.add(primary_key)
                        concatenated_primary_keys.append(
                            {PRIMARY_KEY_ATTRIBUTE_NAME_VALUE: primary_key}
                        )

            batch_keys[table] = concatenated_primary_keys
            attribute_map[table] = feature_names + [PRIMARY_KEY_ATTRIBUTE_NAME_VALUE]

        response = self._paginated_batch_get(batch_keys, attribute_map, metrics=metrics)
        return self._dynamodb_batch_to_pandas(
            response, primary_key_dict, feature_names_dict, metrics=metrics
        )

    def _paginated_batch_get(
        self,
        batch_keys: Dict[str, List[Any]],
        attribute_map: Dict[str, List[str]],
        *,
        metrics: LookupClientMetrics = None,
        batch_size=BATCH_GET_ITEM_LIMIT,
    ) -> Dict[str, List[Any]]:
        """
        Make paginated get batch item request to Amazon DynamoDB.
        :param batch_keys: dictionary from online feature table name to a list of items to retrieve
        :param attribute_map:  dictionary from online feature table name to feature names.
        """
        # Format for calling _do_batch_get.
        # batch_keys_for_table = {
        #     "Keys": items.
        #     "AttributesToGet": feature_names
        # }
        paginated_keys = paginate_keys(batch_keys, batch_size)
        batched_results = []
        for batch in paginated_keys:
            batch_keys_dyanmodb_format = {}
            for table in batch.keys():
                batch_keys_dyanmodb_format[table] = {
                    KEYS: batch[table],
                    ATTRIBUTES_TO_GET: attribute_map[table],
                }
            batched_results.append(
                self._do_batch_get(batch_keys_dyanmodb_format, metrics=metrics)
            )

        return merge_batched_results(batched_results)

    # Modified from code example
    # https://docs.aws.amazon.com/code-samples/latest/catalog/python-dynamodb-batching-dynamo_batching.py.html
    def _do_batch_get(
        self, batch_keys: Dict[str, Dict], *, metrics: LookupClientMetrics = None
    ) -> Dict[str, List]:
        """
        Gets a batch of items from Amazon DynamoDB. Batches can contain keys from
        more than one table.

        When Amazon DynamoDB cannot process all items in a batch, a set of unprocessed
        keys is returned. This function uses an deterministic exponential backoff algorithm to retry
        getting the unprocessed keys until all are retrieved or the specified
        number of tries is reached.

        A single operation can retrieve up to 16 MB of data, which can contain as many as 100 items.

        :param batch_keys: The set of tables to retrieve from. A batch can contain at most 100
                           keys. Otherwise, Amazon DynamoDB returns an error.
        :return: The dictionary of retrieved items grouped under their respective
                 table names.
        """
        num_retry = 0
        max_tries = 3
        backoff_in_seconds = (
            1  # Start with 1 second of sleep, then exponentially increase.
        )
        aggregated_response = {key: [] for key in batch_keys}
        unprocessed_keys = []
        while num_retry < max_tries:
            batch_get_item = lookup_call_maybe_with_metrics(
                self._dynamodb_resource.batch_get_item, metrics
            )
            response = batch_get_item(RequestItems=batch_keys)

            # Collect any retrieved items and retry unprocessed keys.
            for key in response.get("Responses", []):
                aggregated_response[key] += response["Responses"][key]
            unprocessed_keys = response["UnprocessedKeys"]
            if len(unprocessed_keys) > 0:
                batch_keys = unprocessed_keys
                unprocessed_count = sum(
                    [len(batch_key["Keys"]) for batch_key in batch_keys.values()]
                )
                _logger.info(
                    "%s unprocessed keys returned. Sleep, then retry.",
                    unprocessed_count,
                )
                num_retry += 1
                if num_retry < max_tries:
                    _logger.info("Sleeping for %s seconds.", backoff_in_seconds)
                    time.sleep(backoff_in_seconds)
                    backoff_in_seconds = min(backoff_in_seconds * 2, 32)
            else:
                break
        if len(unprocessed_keys) > 0:
            raise ValueError(
                "DynamoDB capacity has been reached please increase the provisioned capacity to "
                "fetch the data."
            )
        return aggregated_response

    def _dynamodb_batch_to_pandas(
        self,
        batch_response: Dict[str, List[Dict]],
        primary_key_dict: Dict[str, Dict[LookupKeyType, List]],
        feature_names_dict: Dict[str, Dict[LookupKeyType, List]],
        *,
        metrics: LookupClientMetrics = None,
    ) -> Dict[str, Dict[LookupKeyType, pd.DataFrame]]:
        """
        Converts raw batch response which is a map from table name to retrieved items into a
        dictionary from table name to lookup key to df map. For each table's items, we will group the
        items by lookup keys and order the items in the order of primary key order for that lookup
        key and convert the dynamoDB type to python compatible type. Any missing rows will be
        substituted with a row of Nan values

        :param batch_response: A dictionary from online table name to a list of items.
        :param primary_key_dict: A dictionary from online table name to a map from lookup key
            to primary key list.
        :param feature_names_dict: A dictionary from online table name to a a map from lookup key to
            list of features to retrieve.
        :return: The dictionary of retrieved items grouped under their respective
                table names and lookup keys.
        """
        batch_sorted_df = {}
        nan_features_count = 0
        for table in self._online_feature_table_names_list:
            if table not in batch_response:
                # skip the tables that are not in this batch.
                continue
            response = batch_response[table]
            sorted_response_by_lookup_key = {}
            for lookup_key, primary_key_rows in primary_key_dict[table].items():
                feature_names = feature_names_dict[table][lookup_key]
                sorted_response = []
                # (TODO: ML-26588): Performance profiling. Consider a left join.
                for pk_val in primary_key_rows:
                    is_item_missing = True
                    for item in response:
                        if item[PRIMARY_KEY_ATTRIBUTE_NAME_VALUE] == pk_val:
                            result = [item.get(f, np.nan) for f in feature_names]
                            nan_features_count += num_missing_feature_values(
                                feature_names, item
                            )
                            sorted_response.append(
                                self._dynamodb_to_pandas(result, feature_names, table)
                            )
                            is_item_missing = False
                            break
                    if is_item_missing:
                        _logger.warning(
                            f"No feature values found in {table} for {pk_val}."
                        )
                        sorted_response.append(np.full(len(feature_names), np.nan))
                        nan_features_count += len(feature_names)
                response_df = pd.DataFrame(sorted_response, columns=feature_names)
                sorted_response_by_lookup_key[lookup_key] = response_df
            batch_sorted_df[table] = sorted_response_by_lookup_key

        if metrics:
            # 0 nan feature count still needs to be recorded to propogate metrics for inference request
            metrics.increase_metric(NAN_FEATURE_COUNT, nan_features_count)

        return batch_sorted_df

    def _validate_online_feature_table(
        self,
    ) -> None:
        def _validate_schema_for_pk_lookup():
            """
            Checks KeySchema equals: [{"AttributeName": "_feature_store_internal__primary_keys", "KeyType": "HASH"}]
            """
            if not key_schemas_equal(key_schema, [PRIMARY_KEY_SCHEMA]):
                raise ValueError(
                    f"Online Table {table_name} primary key schema is not configured properly."
                )

        def _validate_schema_for_range_lookup():
            """
            Checks KeySchema equals, in any order:
            [
                {"AttributeName": "_feature_store_internal__primary_keys", "KeyType": "HASH"},
                {"AttributeName": <timestamp key>, "KeyType": "RANGE"},
            ]
            """
            range_schema = to_range_schema(self._timestamp_keys_map[table_name][0].name)
            if not key_schemas_equal(key_schema, [PRIMARY_KEY_SCHEMA, range_schema]):
                raise ValueError(
                    f"Online Table {table_name} composite key schema is not configured properly."
                )

        # Fetch the online feature table from online store as specified by the OnlineFeatureTable if
        # exists else throw an error.
        for table_name in self._online_feature_table_names_list:
            try:
                table_desc = self._dynamodb_client.describe_table(TableName=table_name)
                # All table descriptions contain the key schema
                key_schema = table_desc[TABLE][KEY_SCHEMA]
            except ClientError as ce:
                raise ce

            if self._query_mode_map[table_name] == QueryMode.PRIMARY_KEY_LOOKUP:
                _validate_schema_for_pk_lookup()
            elif self._query_mode_map[table_name] == QueryMode.RANGE_QUERY:
                _validate_schema_for_range_lookup()
            else:
                raise ValueError(
                    f"Unsupported query mode: {self._query_mode_map[table_name]}"
                )

    def _lookup_primary_key(
        self,
        dynamodb_primary_key: Dict[str, str],
        feature_names: List[str],
        *,
        metrics: LookupClientMetrics = None,
    ):
        table = self._dynamodb_resource.Table(self._online_feature_table_names_list[0])
        lookup_pk = lookup_call_maybe_with_metrics(table.get_item, metrics)
        response = lookup_pk(
            Key=dynamodb_primary_key,
            AttributesToGet=feature_names,
        )

        # Response is expected to have form {"Item": {...}, ...}
        return response.get(ITEM, None)

    def _lookup_range_query(
        self,
        dynamodb_primary_key: Dict[str, str],
        feature_names: List[str],
        *,
        metrics: LookupClientMetrics = None,
    ):
        table = self._dynamodb_resource.Table(self._online_feature_table_names_list[0])
        lookup_range = lookup_call_maybe_with_metrics(table.query, metrics)
        response = lookup_range(
            ScanIndexForward=False,
            Limit=1,
            KeyConditionExpression=Key(PRIMARY_KEY_ATTRIBUTE_NAME_VALUE).eq(
                dynamodb_primary_key[PRIMARY_KEY_ATTRIBUTE_NAME_VALUE]
            ),
            **to_safe_select_expression(feature_names),
        )

        # Response is expected to have form {"Items": [{...}], ...}
        items = response.get(ITEMS, [])
        return items[0] if len(items) else None

    def _pandas_to_dynamodb_primary_keys(
        self, table_name: str, lookup_row: List[Tuple[str, Any]]
    ):
        dynamodb_lookup_row = self._pandas_to_dynamodb(table_name, lookup_row)
        dynamodb_primary_key = to_dynamodb_primary_key(dynamodb_lookup_row)
        return dynamodb_primary_key[PRIMARY_KEY_ATTRIBUTE_NAME_VALUE]

    def _run_lookup_dynamodb_query(
        self,
        feature_names: List[str],
        feature_table_name: str,
        lookup_row: List[Tuple[str, Any]],
        *,
        metrics: LookupClientMetrics = None,
    ):
        """
        This helper function executes a single DynamoDB query.
        """
        dynamodb_lookup_row = self._pandas_to_dynamodb(feature_table_name, lookup_row)
        dynamodb_primary_key = to_dynamodb_primary_key(dynamodb_lookup_row)

        if self._query_mode_map[feature_table_name] == QueryMode.PRIMARY_KEY_LOOKUP:
            feature_values = self._lookup_primary_key(
                dynamodb_primary_key, feature_names, metrics=metrics
            )
        elif self._query_mode_map[feature_table_name] == QueryMode.RANGE_QUERY:
            feature_values = self._lookup_range_query(
                dynamodb_primary_key, feature_names, metrics=metrics
            )
        else:
            raise ValueError(f"Unsupported query mode: {self.query_mode}")

        if not feature_values:
            _logger.warning(
                f"No feature values found in {feature_table_name} for {dynamodb_lookup_row}."
            )
            return np.full(len(feature_names), np.nan)

        # Return the result
        results = [feature_values.get(f, np.nan) for f in feature_names]
        if metrics:
            metrics.increase_metric(
                NAN_FEATURE_COUNT,
                num_missing_feature_values(feature_names, feature_values),
            )
        return self._dynamodb_to_pandas(results, feature_names, feature_table_name)

    def _pandas_to_dynamodb(
        self, feature_table_name: str, row: List[Tuple[str, Any]]
    ) -> List[Any]:
        """
        Converts the input Pandas row to dynamodb compatible python types based on
        the input.
        :return:list[string, ...]
        """
        return [
            self._primary_keys_to_type_converter_map[feature_table_name][
                pk_name
            ].to_online_store(pk_value)
            for pk_name, pk_value in row
        ]

    def _dynamodb_to_pandas(
        self, results: List[Any], feature_names: List[str], feature_table_name: str
    ) -> List[Any]:
        """
        Converts the input results list with dynamodb-compatible python values to pandas types based on
        the input features_names and features converter.
        :return:List[Any]
        """
        feature_names_and_values = zip(feature_names, results)
        return [
            self._features_to_type_converter_map[feature_table_name][
                feature_name
            ].to_pandas(feature_value)
            for feature_name, feature_value in feature_names_and_values
        ]

    def shutdown(self) -> None:
        """
        Cleans up the store connection if it exists on the DynamoDB online store.
        :return:
        """
        # DynamoDB connections are stateless http connections and hence do not need an explicit
        # shutdown operation.
        pass
