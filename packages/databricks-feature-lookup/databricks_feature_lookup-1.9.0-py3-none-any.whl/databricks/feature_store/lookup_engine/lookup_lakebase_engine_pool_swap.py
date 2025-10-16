import functools
import logging
import os
import random
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union

import jwt
import numpy as np
import psycopg2
import sqlalchemy
from sqlalchemy import bindparam, column, select, table, text, tuple_
from sqlalchemy.sql.elements import quoted_name

from databricks.feature_store.lookup_engine.lookup_sql_engine import LookupSqlEngine
from databricks.feature_store.lookup_engine.oauth_token_manager import OAuthTokenManager
from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.feature_store.utils.lakebase_constants import (
    LAKEBASE_OAUTH_TOKEN_FILE_PATH,
)
from databricks.feature_store.utils.logging_utils import get_logger
from databricks.feature_store.utils.metrics_utils import LookupClientMetrics
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
)

FEATURE_SERVING_LAKEBASE_CONNECTION_RECYCLE_SECONDS = (
    "FEATURE_SERVING_LAKEBASE_CONNECTION_RECYCLE_SECONDS"
)
FEATURE_SERVING_LAKEBASE_POOL_SWAP_SECONDS = (
    "FEATURE_SERVING_LAKEBASE_POOL_SWAP_SECONDS"
)
FIELD_NAME_FOR_ROLE_IN_TOKEN = "sub"
JWT_ALGORITHM = "RS256"
BASE_URL = "postgresql+psycopg2://"

CONNECTION_POOL_SIZE = 10
CONNECTION_POOL_MAX_OVERFLOW = 0

_logger = get_logger(__name__, log_level=logging.INFO)


class LookupLakebaseEnginePoolSwap(LookupSqlEngine):
    """
    This is a legacy version of LookupLakebaseEngine that uses a connection pool swapping mechanism.
    We want to keep this implementation momentarily until it's validated in real production use cases
    from some customers.
    All new features should go into LookupLakebaseEngine instead. And we should remove this implementation soon.
    TODO[ML-58447]: remove this implementation.
    """

    _engine_cache = {}
    _pool_warmer_registry = {}

    def __init__(
        self, online_feature_table: OnlineFeatureTable, ro_user: str, ro_password: str
    ):
        self.connection_recycle_seconds = int(
            os.environ.get(FEATURE_SERVING_LAKEBASE_CONNECTION_RECYCLE_SECONDS, "900")
        )
        self.pool_swap_seconds = int(
            os.environ.get(FEATURE_SERVING_LAKEBASE_POOL_SWAP_SECONDS, "850")
        )
        # Initialize query cache dictionary
        self.queries = {}
        self._oauth_token_manager = OAuthTokenManager(
            oauth_token_file_path=LAKEBASE_OAUTH_TOKEN_FILE_PATH,
            password_override=ro_password,
        )
        # The parent constructor calls get_connection which requires the oauth token to be set.
        # So we need to set the oauth token manager before calling super().__init__
        super().__init__(online_feature_table, ro_user, ro_password)
        self._oauth_token_manager.start_token_refresh_thread()
        # Start a background thread to keep the connection pool warm
        if self._get_engine_cache_key() not in self._pool_warmer_registry:
            pool_warmer_thread = threading.Thread(target=self._pool_warmer, daemon=True)
            self._pool_warmer_registry[
                self._get_engine_cache_key()
            ] = pool_warmer_thread
            self.run_pool_warmer = True
            pool_warmer_thread.start()
        else:
            self.run_pool_warmer = False

    def _get_engine_cache_key(self):
        return (self.host, self.port, self.database_name)

    def _pool_warmer(self):
        # Interval for swapping the pool
        interval = self.pool_swap_seconds
        while interval > 0 and self.run_pool_warmer:
            try:
                # Create a new engine instance
                new_engine = self._create_new_engine()

                # Warm the new engine's connection pool
                warm_connections = []
                try:
                    # Open multiple connections to populate the pool
                    for i in range(CONNECTION_POOL_SIZE):  # Warm all pool connections
                        swap_request_time = time.time()
                        conn = new_engine.connect()
                        swap_warm_time = time.time() - swap_request_time
                        conn.execute(text("SELECT 1"))
                        warm_connections.append(conn)

                    for conn in warm_connections:
                        conn.close()

                    # Atomically swap engines
                    engine_cache_key = self._get_engine_cache_key()
                    old_engine = self._engine_cache.get(engine_cache_key)
                    self._engine_cache[engine_cache_key] = new_engine

                    # Dispose of old engine if it exists
                    if old_engine is not None:
                        old_engine.dispose()

                except Exception as warm_error:
                    # If warming fails, dispose the new engine and keep using the old one
                    _logger.error("Pool warming failed: %s", warm_error)
                    # Clean up any open warming connections
                    for conn in warm_connections:
                        try:
                            conn.close()
                        except:
                            pass
                    new_engine.dispose()
            except Exception as e:
                _logger.error("Failed to create new engine: %s", e)
            jitter = random.randint(0, 10)
            time.sleep(interval + jitter)

    def stop_pool_warmer(self):
        """
        Stop the pool warmer thread. This is useful for cleanup after tests.
        """
        self.run_pool_warmer = False
        self._pool_warmer_registry[self._get_engine_cache_key()].join()

    def _create_new_engine(self):
        """Create a new SQLAlchemy engine instance."""
        pool_recycle = self.connection_recycle_seconds
        # Add randomization to distribute connection recycling
        pool_recycle_with_jitter = pool_recycle + random.randint(0, 10)

        new_engine = sqlalchemy.create_engine(
            BASE_URL,
            creator=self._connect,
            pool_size=CONNECTION_POOL_SIZE,
            max_overflow=CONNECTION_POOL_MAX_OVERFLOW,
            pool_timeout=2,
            pool_recycle=pool_recycle_with_jitter,
        )
        return new_engine

    # Override
    def _get_database_and_table_name(
        self, online_table_name
    ) -> Tuple[str, Optional[str], str]:
        name_components = online_table_name.split(".")
        if len(name_components) != 3:
            raise ValueError(
                f"Online table name {online_table_name} is misformatted and must be in 3L format for Lakebase stores"
            )
        return (name_components[0], name_components[1], name_components[2])

    # Override
    def is_lakebase_engine(self) -> bool:
        return True

    # Lakebase sql connection uses a connection pool
    # Override
    @contextmanager
    def _get_connection(self):
        if self._get_engine_cache_key() in self._engine_cache:
            engine = self._engine_cache[self._get_engine_cache_key()]
        else:
            _logger.info(f"No engine in cache, creating new one")
            engine = self._create_new_engine()
            self._engine_cache[self._get_engine_cache_key()] = engine

        request_connection_time = time.time()
        connection = engine.connect()
        get_connection_time = time.time() - request_connection_time
        if get_connection_time > 0.08:
            _logger.warning(
                f"Slow connection acquisition: {get_connection_time*1000}ms;"
            )
        # When the caller invokes "with _get_connection() as x", the connection will be returned as "x"
        yield connection

        # Everything below here will be executed in contextmanager.__exit__()
        # With connection pooling, .close() only returns the connection to the pool instead of closing it.
        connection.close()

    def _connect(self):
        oauth_token_or_password = (
            self._oauth_token_manager.get_oauth_token_or_password()
        )
        # self.user is parsed from EnvVar. If not set, parse the client_id
        # from the oauth token
        db_user = self.user
        if not db_user:
            content = jwt.decode(
                oauth_token_or_password,
                algorithms=[JWT_ALGORITHM],
                # No worry, the token is validated by Postgres
                options={"verify_signature": False},
            )
            db_user = content[FIELD_NAME_FOR_ROLE_IN_TOKEN]

        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.database_name,
            user=db_user,
            password=oauth_token_or_password,
            sslmode="require",
        )

    # Override
    def _database_contains_feature_table(self, sql_connection):
        # TODO[ML-53997]: implement validation
        return True

    # Override
    def _database_contains_primary_keys(self, sql_connection):
        # TODO[ML-53997]: implement validation
        return True

    # Override
    @classmethod
    def _sql_safe_name(cls, name):
        return name

    # Override with batch optimization for lakebase engine
    def _get_sql_results(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
        metrics: LookupClientMetrics = None,  # Ignored for lakebase engine
    ) -> List[Union[Dict[str, Any], np.ndarray, sqlalchemy.engine.Row]]:
        # For empty lookup list, return empty results
        if not lookup_list.rows:
            return []

        # Create cache key from columns and feature names (including whether single or multi-key)
        is_single_key = len(lookup_list.columns) == 1
        cache_key = (tuple(lookup_list.columns), tuple(feature_names), is_single_key)

        # Check if we have a cached query for this combination
        if cache_key in self.queries:
            query = self.queries[cache_key]
        else:
            # Create table reference with schema
            quoted_table_name = quoted_name(self.table_name, quote=True)
            quoted_schema_name = (
                quoted_name(self.schema_name, quote=True) if self.schema_name else None
            )
            table_ref = table(quoted_table_name, schema=quoted_schema_name)

            # Create column references
            pk_columns = [
                column(quoted_name(pk, quote=True)) for pk in lookup_list.columns
            ]
            feature_columns = [
                column(quoted_name(f, quote=True)) for f in feature_names
            ]

            # Build the SELECT query with WHERE clause template
            base_query = select(*pk_columns, *feature_columns).select_from(table_ref)

            # Add WHERE clause with parameter binding template
            if is_single_key:
                # Single primary key: WHERE pk IN (:values)
                pk_col = pk_columns[0]
                query = base_query.where(
                    pk_col.in_(bindparam("values", expanding=True))
                )
            else:
                # Multiple primary keys: WHERE (pk1, pk2) IN (:value_tuples)
                pk_tuple = tuple_(*pk_columns)
                query = base_query.where(
                    pk_tuple.in_(bindparam("value_tuples", expanding=True))
                )

            # Cache the complete query for future use
            self.queries[cache_key] = query

        # Prepare parameters for the cached query
        if is_single_key:
            values = [row[0] for row in lookup_list.rows]
            params = {"values": values}
        else:
            value_tuples = [tuple(row) for row in lookup_list.rows]
            params = {"value_tuples": value_tuples}

        with self._get_connection() as sql_connection:
            sql_data = sql_connection.execute(query, params)
            # Rows in results may not be in the same order as the lookup list.
            results = sql_data.fetchall()

            # Create a mapping from primary key values to result rows for fast lookup
            pk_to_result = {}
            for result_row in results:
                # Extract primary key values from the result (first len(lookup_list.columns) columns)
                pk_values = tuple(result_row[: len(lookup_list.columns)])
                # Extract feature values (remaining columns)
                feature_values = result_row[len(lookup_list.columns) :]
                pk_to_result[pk_values] = feature_values

            # Build ordered results matching the original lookup order
            ordered_results = []
            for row in lookup_list.rows:
                pk_tuple = tuple(row)
                if pk_tuple in pk_to_result:
                    # Create a dictionary directly
                    feature_values = pk_to_result[pk_tuple]
                    ordered_results.append(dict(zip(feature_names, feature_values)))
                else:
                    # No result found for this primary key - return None values
                    _logger.warning(
                        f"No feature values found in {self.table_name} for primary key {dict(zip(lookup_list.columns, row))}."
                    )
                    ordered_results.append({name: None for name in feature_names})

            return ordered_results
