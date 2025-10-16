import logging
import os
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pandas as pd

from databricks.feature_store.lookup_engine import (
    AwsAccessKey,
    LookupCosmosDbEngine,
    LookupDynamoDbEngine,
    LookupLakebaseEngine,
    LookupLakebaseEnginePoolSwap,
    LookupLegacyBrickstoreHttpEngine,
    LookupMySqlEngine,
    LookupSqlEngine,
    LookupSqlServerEngine,
)
from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.feature_store.utils.lakebase_constants import (
    BRICKSTORE_OAUTH_TOKEN_FILE_PATH,
    LAKEBASE_USER,
)
from databricks.feature_store.utils.logging_utils import get_logger
from databricks.feature_store.utils.metrics_utils import LookupClientMetrics
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
)
from databricks.ml_features_common.entities.query_mode import QueryMode
from databricks.ml_features_common.entities.store_type import StoreType

_logger = get_logger(__name__, log_level=logging.INFO)


# The provisioner of this model is expected to set the following environment variable for each
# feature table if the feature store is SQL based:
#  (1) <online_store_for_serving.read_secret_prefix>_USER
#  (2) <online_store_for_serving.read_secret_prefix>_PASSWORD
USER_SUFFIX = "_USER"
PASSWORD_SUFFIX = "_PASSWORD"
# Prefix for Lakebase user and password from environment variable
LAKEBASE_PREFIX = "LAKEBASE"
# For DynamoDB the following variables should be set:
#  (1) <online_store_for_serving.read_secret_prefix>_ACCESS_KEY_ID
#  (2) <online_store_for_serving.read_secret_prefix>_SECRET_ACCESS_KEY
ACCESS_KEY_ID_SUFFIX = "_ACCESS_KEY_ID"
SECRET_ACCESS_KEY_SUFFIX = "_SECRET_ACCESS_KEY"
# For Cosmos DB the following variable should be set:
#  (1) <online_store_for_serving.read_secret_prefix>_AUTHORIZATION_KEY
AUTHORIZATION_KEY_SUFFIX = "_AUTHORIZATION_KEY"
LookupKeyType = Tuple[str, ...]
# Engine configurations
DISABLE_CONNECTION_POOL = "DISABLE_CONNECTION_POOL"
# Enable lakebase engine with custom connection pool
# TODO[ML-58447]: remove this environment variable.
KEEP_CONNECTIONS_ALIVE = "KEEP_CONNECTIONS_ALIVE"


def generate_lookup_sql_engine(
    online_feature_table: Union[OnlineFeatureTable, List[OnlineFeatureTable]],
    creds: Tuple[str, str],
) -> LookupSqlEngine:
    if isinstance(online_feature_table, List):
        raise Exception(f"Internal error: Batch lookup is unsupported in SQL Engine.")

    ro_user, ro_password = creds
    if (
        online_feature_table.online_store.store_type == StoreType.BRICKSTORE
        or online_feature_table.online_store.store_type
        == StoreType.DATABRICKS_ONLINE_STORE
    ):
        if os.environ.get(KEEP_CONNECTIONS_ALIVE, "false") == "true":
            _logger.info("Using lakebase engine with connections kept alive")
            return LookupLakebaseEngine(online_feature_table, ro_user, ro_password)
        else:
            _logger.info("Using legacy lakebase engine with pool swapping")
            return LookupLakebaseEnginePoolSwap(
                online_feature_table, ro_user, ro_password
            )
    elif online_feature_table.online_store.store_type == StoreType.SQL_SERVER:
        return LookupSqlServerEngine(online_feature_table, ro_user, ro_password)
    return LookupMySqlEngine(online_feature_table, ro_user, ro_password)


def generate_lookup_dynamodb_engine(
    online_feature_table: Union[OnlineFeatureTable, List[OnlineFeatureTable]],
    creds: Optional[Tuple[str, str]],
) -> LookupDynamoDbEngine:
    if creds:
        access_key_id, secret_access_key = creds

        return LookupDynamoDbEngine(
            online_feature_table,
            access_key=AwsAccessKey(access_key_id, secret_access_key),
        )
    else:
        return LookupDynamoDbEngine(online_feature_table, access_key=None)


def generate_lookup_cosmosdb_engine(
    online_feature_table: Union[OnlineFeatureTable, List[OnlineFeatureTable]],
    creds: str,
) -> LookupCosmosDbEngine:
    if isinstance(online_feature_table, List):
        raise Exception(f"Internal error: Batch lookup is unsupported in Cosmos DB.")
    return LookupCosmosDbEngine(online_feature_table, authorization_key=creds)


def generate_lookup_legacy_brickstore_http_engine(
    online_feature_table: Union[OnlineFeatureTable, List[OnlineFeatureTable]],
) -> LookupLegacyBrickstoreHttpEngine:
    disable_connection_pool = os.environ.get(DISABLE_CONNECTION_POOL, "false") == "true"
    return LookupLegacyBrickstoreHttpEngine(
        online_feature_table, disable_connection_pool
    )


def load_credentials_from_env(online_ft: OnlineFeatureTable):
    def get_env_var(env_var_suffix: str) -> str:
        env_var = ""
        if (
            online_ft.online_store.store_type == StoreType.BRICKSTORE
            or online_ft.online_store.store_type == StoreType.DATABRICKS_ONLINE_STORE
        ):
            env_var = LAKEBASE_PREFIX + env_var_suffix
        else:
            env_var = online_ft.online_store.read_secret_prefix + env_var_suffix
            if env_var not in os.environ:
                raise Exception(
                    f"Internal error: {env_var} not found for feature table {online_ft.feature_table_name}."
                )
        return os.getenv(env_var)

    if online_ft.online_store.store_type == StoreType.DYNAMODB:
        try:
            return (
                get_env_var(ACCESS_KEY_ID_SUFFIX),
                get_env_var(SECRET_ACCESS_KEY_SUFFIX),
            )
        except:
            # It is assumed that if the secrets are not configured, the lookup will be authorized
            # using instance profile. This is validated in serving-scheduler on endpoint creation
            # see EndpointDeploymentProvisioner.verifyAndMaybeUpdateFsMetadataForInstanceProfile
            # TODO (ML-33307): add env var check whether instance profile is configured
            print(
                "Secret credentials not configured, attempting to use cluster instance profile."
            )
            return None
    elif online_ft.online_store.store_type == StoreType.COSMOSDB:
        return get_env_var(AUTHORIZATION_KEY_SUFFIX)
    return (
        get_env_var(USER_SUFFIX),
        get_env_var(PASSWORD_SUFFIX),
    )


# TODO(ML-26146): refactor this method and above helpers to appropriate seperate util files
def tables_share_dynamodb_access_keys(
    online_feature_tables: List[OnlineFeatureTable],
):
    # check region and credentials to see if all feature tables are using same DynamoDB accesss keys
    region, creds = None, None
    for ft in online_feature_tables:
        if ft.online_store.store_type != StoreType.DYNAMODB:
            return False
        elif region == None:
            region = ft.online_store.extra_configs.region
            creds = load_credentials_from_env(ft)
        elif (
            region != ft.online_store.extra_configs.region
            or load_credentials_from_env(ft) != creds
        ):
            return False
    return True


def can_use_brickstore_http_gateway(
    online_feature_tables: Union[OnlineFeatureTable, List[OnlineFeatureTable]]
):
    if isinstance(online_feature_tables, OnlineFeatureTable):
        online_feature_tables = [online_feature_tables]
    return (
        all(
            [
                oft.online_store.store_type == StoreType.BRICKSTORE
                or oft.online_store.store_type == StoreType.DATABRICKS_ONLINE_STORE
                for oft in online_feature_tables
            ]
        )
        and len(online_feature_tables) > 0
        and online_feature_tables[0].online_store.extra_configs.table_serving_url != ""
        and os.path.exists(BRICKSTORE_OAUTH_TOKEN_FILE_PATH)
    )


def is_primary_key_lookup(
    online_feature_tables: List[OnlineFeatureTable],
):
    for oft in online_feature_tables:
        mode = oft.online_store.query_mode
        if mode == QueryMode.RANGE_QUERY:
            return False
        elif mode == QueryMode.PRIMARY_KEY_LOOKUP:
            continue
        else:
            raise ValueError(f"Unsupported query mode: {mode}")
    return True


class OnlineLookupClient:
    def __init__(
        self,
        online_feature_table: Union[OnlineFeatureTable, List[OnlineFeatureTable]],
        eligible_for_pgsql: bool = False,
    ):
        self.lookup_engine = self._generate_lookup_engine(
            online_feature_table, eligible_for_pgsql
        )

    @classmethod
    def _generate_lookup_engine(
        cls,
        online_feature_table: Union[OnlineFeatureTable, List[OnlineFeatureTable]],
        eligible_for_pgsql: bool,
    ):
        first_online_feature_table = None
        if isinstance(online_feature_table, List):
            if len(online_feature_table) == 0:
                raise Exception(
                    f"Internal Error: No feature table passed while creating lookup engine."
                )
            first_online_feature_table = online_feature_table[0]
        else:
            first_online_feature_table = online_feature_table

        creds = load_credentials_from_env(first_online_feature_table)
        if first_online_feature_table.online_store.store_type == StoreType.DYNAMODB:
            return generate_lookup_dynamodb_engine(online_feature_table, creds)
        elif first_online_feature_table.online_store.store_type == StoreType.COSMOSDB:
            return generate_lookup_cosmosdb_engine(online_feature_table, creds)
        elif (
            first_online_feature_table.online_store.store_type
            in {StoreType.BRICKSTORE, StoreType.DATABRICKS_ONLINE_STORE}
            and can_use_brickstore_http_gateway(online_feature_table)
            and not eligible_for_pgsql
        ):
            return generate_lookup_legacy_brickstore_http_engine(online_feature_table)
        return generate_lookup_sql_engine(online_feature_table, creds)

    def batch_lookup_features(
        self,
        lookup_list_dict: Dict[str, Dict[LookupKeyType, LookupKeyList]],
        feature_names_dict: Dict[str, Dict[LookupKeyType, List[str]]],
        *,
        metrics: LookupClientMetrics = None,
    ) -> Dict[str, Dict[LookupKeyType, pd.DataFrame]]:
        """
        :param lookup_list_dict: dictionary from online feature table name to a dictionary from
            lookup key to primary key list.
        :param feature_names_dict:  dictionary from online feature table name to feature names.
        :return a Dictionary from online feature table name to feature values.
        """
        return self.lookup_engine.batch_lookup_features(
            lookup_list_dict, feature_names_dict, metrics=metrics
        )

    def lookup_features(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
        *,
        metrics: LookupClientMetrics = None,
    ) -> pd.DataFrame:
        """Uses a Python database connection to lookup features in feature_names using
        the lookup keys and values in lookup_list. The online store database and table name are
        obtained from the OnlineFeatureTable passed to the constructor.

        The resulting DataFrame has the same number of rows as lookup_list. In the case that a
        lookup key cannot be found, a row of NaNs will be returned in the resulting DataFrame.

        Throws an exception if the table, lookup keys, or feature columns do not exist in the
        online store.

        :param lookup_list: Should contain one column for each primary key of the online feature
        table, and one row for each entity to look up.
        :param feature_names: A list of feature names to look up.
        :return: Pandas DataFrame containing feature keys and values fetched from the online store.
        """
        features = self.lookup_engine.lookup_features(
            lookup_list, feature_names, metrics=metrics
        )
        return features

    def lookup_feature_dicts(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
    ) -> List[Dict[str, Any]]:
        return self.lookup_engine.lookup_feature_dicts(lookup_list, feature_names)

    def cleanup(self):
        """
        Performs any cleanup associated with the online store.
        :return:
        """
        self.lookup_engine.shutdown()
