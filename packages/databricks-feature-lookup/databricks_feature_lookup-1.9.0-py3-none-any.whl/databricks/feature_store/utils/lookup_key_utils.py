from typing import List, Tuple

import pandas as pd

from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
    PrimaryKeyDetails,
)
from databricks.ml_features_common.protos.feature_store_serving_pb2 import (
    DataType as ProtoDataType,
)

LookupKeyType = Tuple[str, ...]


def validate_lookup_key_datatype(
    df: pd.DataFrame,
    primary_keys: List[PrimaryKeyDetails],
    lookup_key: LookupKeyType,
):
    """
    Validates that the given keys are of the correct datatype used to look up from online store.
    It is assumed that lookup_key and primary_keys are in the same order.
    """
    dtypes_dict = df.dtypes.to_dict()
    for pk, lookup_name in zip(primary_keys, lookup_key):
        if pk.data_type == ProtoDataType.STRING and not pd.api.types.is_string_dtype(
            dtypes_dict[lookup_name]
        ):
            raise ValueError(f"Provided primary keys {pk.name} is not of type string")


def get_primary_key_list(
    lookup_key: LookupKeyType,
    primary_keys: List[PrimaryKeyDetails],
    df: pd.DataFrame,
) -> LookupKeyList:
    """
    :return: A list of rows where each row is a list of tuples, each tuple is (column_name, value).
        There will be a column per column in `primary_keys`, and a row per row in `df`. `lookup_key` must `primary_keys` in length.
        The order of columns in each row is the same as the order of columns in `primary_keys`.
        Note that using LookupKeyList (which uses Python lists) is faster than using pandas
        DataFrame for the majority of use cases, since pandas DataFrame is optimized for large
        number of rows and has heavy overhead for small data.
        It is assumed that lookup_key and primary_keys are in the same order.
    """
    lookup_key_columns = df[list(lookup_key)]
    validate_lookup_key_datatype(lookup_key_columns, primary_keys, lookup_key)
    lookup_key_dict = lookup_key_columns.to_dict("list")
    # Update the lookup_key_df column names to be those of the feature table primary
    # key columns, rather than the names of columns from the source DataFrame. This is
    # required by the lookup_features interface.
    return LookupKeyList(
        columns=[feature_pk.name for feature_pk in primary_keys],
        rows=[
            [lookup_key_dict[lookup_name][i] for lookup_name in lookup_key]
            for i in range(len(df))
        ],
    )
