from collections import defaultdict
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter

from databricks.feature_store.lookup_engine.lookup_engine import LookupEngine
from databricks.feature_store.lookup_engine.oauth_token_manager import OAuthTokenManager
from databricks.feature_store.utils.brickstore_http_type_utils import (
    BRICKSTORE_HTTP_DATA_TYPE_CONVERTER_FACTORY,
)
from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.feature_store.utils.lakebase_constants import (
    BRICKSTORE_OAUTH_TOKEN_FILE_PATH,
)
from databricks.feature_store.utils.metrics_utils import (
    LookupClientMetrics,
    lookup_call_maybe_with_metrics,
)
from databricks.feature_store.utils.retry_utils import RetryWithLogging
from databricks.feature_store.utils.trace_utils import trace_latency
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
)

LookupKeyType = Tuple[str, ...]


class LookupLegacyBrickstoreHttpEngine(LookupEngine):
    """
    Read online features from Brickstore by making requests aginst the HTTP gateway.
    """

    def __init__(
        self,
        online_feature_tables: Union[OnlineFeatureTable, List[OnlineFeatureTable]],
        disable_connection_pool: bool = False,
    ):
        # Table serving URL will be the same for all tables, so we can read the first.
        # Consistency is enforced by the control plane.
        if isinstance(online_feature_tables, OnlineFeatureTable):
            online_feature_tables = [online_feature_tables]

        self._table_serving_url = online_feature_tables[
            0
        ].online_store.extra_configs.table_serving_url

        if not disable_connection_pool:
            self._connection = self._new_session()
        else:
            self._connection = requests

        self._oauth_token_manager = OAuthTokenManager(
            oauth_token_file_path=BRICKSTORE_OAUTH_TOKEN_FILE_PATH,
        )
        self._oauth_token_manager.start_token_refresh_thread()

        self._columns_to_type_converter_map = {
            oft.online_feature_table_name: {
                col.name: BRICKSTORE_HTTP_DATA_TYPE_CONVERTER_FACTORY.get_converter(col)
                for col in oft.primary_keys + oft.features
            }
            for oft in online_feature_tables
        }

    @staticmethod
    def _new_session() -> requests.Session:
        session = requests.Session()
        # Retry on the given list of status and connection errors e.g. RemoteDisconnected.
        # When the retry attempt is exhausted, if the last error was a status code, the response
        # will be returned. Otherwise, if the last error was an exception, it will be raised.
        retry = RetryWithLogging(
            total=3,
            backoff_factor=0.2,
            status_forcelist=[429, 500, 502, 503, 504],
            # Default methods to be used for allowed_methods
            # We are adding POST into the method
            # DEFAULT_ALLOWED_METHODS = frozenset({'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PUT', 'TRACE'})
            # See https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html#urllib3.util.Retry.DEFAULT_ALLOWED_METHODS
            allowed_methods=frozenset(
                ["DELETE", "GET", "HEAD", "OPTIONS", "PUT", "TRACE", "POST"]
            ),
            raise_on_status=False,
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session

    def _pandas_to_json_input_dict(
        self, feature_table_name: str, row: List[Tuple[str, Any]]
    ) -> Dict[str, Any]:
        """
        Converts the input Pandas row to JSON inputs
        """
        return {
            col_name: self._columns_to_type_converter_map[feature_table_name][
                col_name
            ].to_online_store(col_value)
            for col_name, col_value in row
        }

    def _raw_response_to_typed(
        self, feature_table_name: str, feature_name: str, feature_value: Any
    ) -> Any:
        """
        Converts the input result with brickstore-returned python values to pandas types based on
        the input features_names and features converter.
        """
        return self._columns_to_type_converter_map[feature_table_name][
            feature_name
        ].to_pandas(feature_value)

    def _lookup_list_dict_to_request_json(
        self,
        lookup_list_dict: Dict[str, Dict[LookupKeyType, LookupKeyList]],
        feature_names_dict: Dict[str, Dict[LookupKeyType, List[str]]],
    ):
        tables_dict = {}

        for oft_name, lookup_to_pk_values_dict in lookup_list_dict.items():
            selected_features_for_table = set()
            pk_input_values_for_table = []

            def convert_fn(row):
                return self._pandas_to_json_input_dict(oft_name, row)

            for lookup_key, pk_list in lookup_to_pk_values_dict.items():
                features_for_this_lookup_key = feature_names_dict[oft_name][lookup_key]
                # Always want to look up PKs.
                selected_features_for_table.update(list(pk_list.columns))
                selected_features_for_table.update(features_for_this_lookup_key)

                lookup_dict = [convert_fn(row) for row in pk_list.items]
                pk_input_values_for_table += lookup_dict

            table_dict = {
                "keys": pk_input_values_for_table,
                "select": list(selected_features_for_table),
            }

            tables_dict[oft_name] = table_dict
        return tables_dict

    def _response_to_looked_up_df_dict(
        self,
        lookup_list_dict: Dict[str, Dict[LookupKeyType, LookupKeyList]],
        feature_names_dict: Dict[str, Dict[LookupKeyType, List[str]]],
        results: Dict,
    ):
        result_dict = defaultdict(lambda: defaultdict(list))

        for oft_name, table_results_dict in results.items():
            if "rows" not in table_results_dict:
                table_results_dict["rows"] = []
            looked_up_data = table_results_dict["rows"]
            col_infos = table_results_dict["schema"]["columns"]

            def convert_fn(feature_name, feature_value):
                return self._raw_response_to_typed(
                    oft_name, feature_name, feature_value
                )

            looked_up_data_columns = [col_info["name"] for col_info in col_infos]
            converted_looked_up_data_dict = {
                looked_up_data_columns[i]: [
                    convert_fn(looked_up_data_columns[i], row[i])
                    for row in looked_up_data
                ]
                for i in range(len(looked_up_data_columns))
            }
            # Example:
            # converted_looked_up_data_dict = {
            #     "a": [1, 3, 5, 7],
            #     "b": [2, 4, 6, 8],
            #     "name": ["abc", "def", "ghi", "jkl"],
            #     "age": [10, 20, 30, 40],
            # }

            lookup_key_to_input_pks_list_dict = lookup_list_dict[oft_name]
            for (
                lookup_key,
                input_pks_list,
            ) in lookup_key_to_input_pks_list_dict.items():
                # Example:
                # input_pks_list = LookupKeyList(columns=["a", "b"], rows=[(1, 2), (3, 4)])

                feat_names_to_look_up = feature_names_dict[oft_name][lookup_key]
                # Example:
                # feat_names_to_look_up = ["name", "age"]

                # Input pks df is raw input from user, so we need to convert it to same types
                # as converted looked up df for merge to work.
                # Compute the converted primary key values in user's request.
                converted_input_pks = [
                    tuple(convert_fn(pk_name, pk_value) for pk_name, pk_value in row)
                    for row in input_pks_list.items
                ]
                # Example: converted_input_pks = [(1, 2), (3, 4)]

                # Compute the converted primary key values in the looked up data.
                converted_looked_up_data_pks = zip(
                    *[
                        converted_looked_up_data_dict[pk_name]
                        for pk_name in input_pks_list.columns
                    ]
                )
                # Example: converted_looked_up_data_pks = [(1, 2), (3, 4), (5, 6), (7, 8)]

                # Construct a dict that maps the converted primary key values in the looked up data
                # to its row index.
                converted_looked_up_data_pks_to_row_index = {
                    pk: i for i, pk in enumerate(converted_looked_up_data_pks)
                }
                # Example:
                # converted_looked_up_data_pks_to_row_index = {
                #     (1, 2): 0,
                #     (3, 4): 1,
                #     (5, 6): 2,
                #     (7, 8): 3,
                # }

                # Produce the final results.
                # For each row, get the looked up values for the requested features.
                def get_result_value(row_index, feat_name):
                    column_values = converted_looked_up_data_dict.get(feat_name, None)
                    if column_values is None:
                        return np.nan

                    return column_values[row_index]

                def get_result_row(input_pk):
                    row_index = converted_looked_up_data_pks_to_row_index.get(
                        input_pk, None
                    )
                    if row_index is None:
                        return np.full(len(feat_names_to_look_up), np.nan)

                    return [
                        get_result_value(row_index, feat_name)
                        for feat_name in feat_names_to_look_up
                    ]

                converted_results = [
                    get_result_row(input_pk) for input_pk in converted_input_pks
                ]
                result_dict[oft_name][lookup_key] = pd.DataFrame(
                    converted_results, columns=feat_names_to_look_up
                )

        return {k: dict(v) for k, v in result_dict.items()}

    def _lookup_and_aggregate_features(self, requested_table_info_dict):
        """
        Send lookup request. If the response contains a page token,
        send requests until there is no page token and aggregate responses.
        """

        @trace_latency("online_feature_store")
        def _send_req(page_token=None, is_retry=False):
            oauth_token = self._oauth_token_manager.get_oauth_token_or_password()
            headers = {"Authorization": f"Bearer {oauth_token}".strip()}
            req_json = {
                "tables": requested_table_info_dict,
            }
            if page_token is not None:
                req_json["page_token"] = page_token
            response = self._connection.post(
                self._table_serving_url, json=req_json, headers=headers
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                if is_retry:
                    raise Exception(f"Expired token: {response.text}")
                else:
                    self._oauth_token_manager.refresh_oauth_token()
                    return _send_req(page_token, is_retry=True)
            elif (
                response.status_code == 400
                and "Server received a request which exceeds maximum allowed content length"
                in response.text
            ):
                raise Exception(
                    f"Request size too large. Please reduce the number of requested rows: {response.text}"
                )
            else:
                raise Exception(f"status_code {response.status_code}: {response.text}")

        resp = _send_req()
        if "results" in resp:
            aggregated_table_info = resp["results"]
        else:
            raise Exception(
                "No online feature information found. Ensure all feature tables are synchronized to an online store."
            )
        while "next_page_token" in resp:
            resp = _send_req(resp["next_page_token"])
            for table, table_info in resp["results"].items():
                if table not in aggregated_table_info:
                    aggregated_table_info[table] = resp["results"][table]
                else:
                    aggregated_table_info[table]["rows"] += table_info["rows"]

        return aggregated_table_info

    def batch_lookup_features(
        self,
        lookup_list_dict: Dict[str, Dict[LookupKeyType, LookupKeyList]],
        feature_names_dict: Dict[str, Dict[LookupKeyType, List[str]]],
        *,
        metrics: LookupClientMetrics = None,
    ) -> Dict[str, Dict[LookupKeyType, pd.DataFrame]]:
        """
        Assume the following lookup_list_dict:
        { table_a: {
          ("my_name",): LookupKeyList(columns=["name_pk"], rows=["x1", "x2"]),
          ("friend_name",): LookupKeyList(columns=["name_pk"], rows=["y1", "y2"])
        }}

        We need to turn into this request JSON:
        {
            "tables": {
                "catalog.schema.table_a": {
                    "keys": [
                        {"name_pk": "x1"},
                        {"name_pk": "y1"},
                        {"name_pk": "x2"},
                        {"name_pk": "y2"}
                    ],
                    "select": ["phone_number", "address"]
                }
            }
        }

        Assuming this provides the response:
        {
            "results": {
                "catalog.schema.table_a": {
                    "schema": {
                        "columns": [
                            {"name": "name", "type_name": "STRING", "nullable": false},
                            {"name": "phone_number", "type_name": "STRING", "nullable": false},
                            {"name": "address", "type_name": "STRING", "nullable": true}
                        ]
                    },
                    "rows": [
                        ["x1", "123", "abc"],
                        ["y1", "456", "def"],
                        ["x2", "789", "ghi"],
                        ["y2", "000", "jkl"],
                    ]
                },
            },
            "next_page_token": "Y2F0YWxvZy5zY2hlbWEudGFibGUyOjE="
        }

        We then need to turn into this map:
        {
            "table_a": {
                ("my_name",): pd.DataFrame({"phone_number": [123, 789]),
                ("friend_name",): pd.DataFrame({"address": [def, jkl})
            }
        }

        """
        tables_info = self._lookup_list_dict_to_request_json(
            lookup_list_dict, feature_names_dict
        )
        lookup_and_aggregate_features = lookup_call_maybe_with_metrics(
            self._lookup_and_aggregate_features, metrics
        )
        looked_up_features = lookup_and_aggregate_features(tables_info)
        return self._response_to_looked_up_df_dict(
            lookup_list_dict, feature_names_dict, looked_up_features
        )

    def lookup_features(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
        *,
        metrics: LookupClientMetrics = None,
    ) -> pd.DataFrame:
        raise NotImplementedError

    def shutdown(self) -> None:
        self._run_token_refresh_thread = False
