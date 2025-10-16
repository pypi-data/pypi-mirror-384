import json
from typing import Any, List

from azure.cosmos.exceptions import CosmosResourceNotFoundError

PARTITION_KEY = "partitionKey"
PATHS = "paths"
PRIMARY_KEY_PROPERTY_NAME_VALUE = "_feature_store_internal__primary_keys"
FEATURE_STORE_SENTINEL_ID_VALUE = "_fs"

DEFAULT_RETRY_CONFIG = {"retry_total": 3, "timeout": 30}


def to_cosmosdb_primary_key(primary_key_values: List[Any]):
    return json.dumps(primary_key_values)


def is_not_found_error(e: Exception) -> bool:
    # Cosmos DB clients are lazily constructed without validation. This results in ContainerProxy.read_item potentially
    # throwing if the account, database, container, or item doesn't exist.
    # Determine if the CosmosResourceNotFoundError was caused by ContainerProxy.read_item finding no result.
    return isinstance(e, CosmosResourceNotFoundError) and e.status_code == 404
