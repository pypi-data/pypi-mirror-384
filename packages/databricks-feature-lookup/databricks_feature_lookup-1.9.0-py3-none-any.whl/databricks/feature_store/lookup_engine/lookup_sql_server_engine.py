import collections
from typing import Optional, Tuple

import sqlalchemy

from databricks.feature_store.lookup_engine.lookup_sql_engine import LookupSqlEngine
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
)


class LookupSqlServerEngine(LookupSqlEngine):
    def __init__(
        self, online_feature_table: OnlineFeatureTable, ro_user: str, ro_password: str
    ):
        super().__init__(online_feature_table, ro_user, ro_password)

    @property
    def engine_url(self):
        return f"mssql+pyodbc://{self.user}:{self.password}@{self.host}:{self.port}/{self.database_name}?driver=ODBC+Driver+17+for+SQL+Server"

    @classmethod
    def _sql_safe_name(cls, name):
        # MSSQL requires [xxx] format to safely handle identifiers that contain special characters or are reserved words.
        return f"[{name}]"

    def _database_contains_feature_table(self, sql_connection):
        query = sqlalchemy.sql.text(
            f"SELECT {self.TABLE_NAME} FROM {self.INFORMATION_SCHEMA}.{self.TABLES} "
            f"WHERE {self.TABLE_CATALOG}='{self.database_name}' AND {self.TABLE_NAME} IN ('{self.table_name}')"
        )
        results = sql_connection.execute(query)
        table = results.fetchall()
        return len(table) > 0

    def _database_contains_primary_keys(self, sql_connection):
        query = sqlalchemy.sql.text(
            f"SELECT col.{self.COLUMN_NAME} FROM {self.INFORMATION_SCHEMA}.{self.TABLE_CONSTRAINTS} tab, {self.INFORMATION_SCHEMA}.{self.CONSTRAINT_COLUMN_USAGE} col "
            f"WHERE tab.{self.TABLE_CATALOG}='{self.database_name}' AND col.{self.TABLE_CATALOG}='{self.database_name}' AND "
            f"col.{self.CONSTRAINT_NAME}=tab.{self.CONSTRAINT_NAME} AND col.{self.TABLE_NAME}=tab.{self.TABLE_NAME} AND "
            f"{self.CONSTRAINT_TYPE}='PRIMARY KEY' AND col.{self.TABLE_NAME}='{self.table_name}'"
        )
        results = sql_connection.execute(query)
        primary_keys = [r[0] for r in results.fetchall()]
        return collections.Counter(primary_keys) == collections.Counter(
            [primary_key.name for primary_key in self.primary_keys]
        )

    # Override
    def _get_database_and_table_name(
        self, online_table_name
    ) -> Tuple[str, Optional[str], str]:
        name_components = online_table_name.split(".")
        if len(name_components) != 2:
            raise ValueError(
                f"Online table name {online_table_name} is misformatted and must be in 2L format for SqlServer stores"
            )
        return (name_components[0], None, name_components[1])
