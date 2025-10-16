from typing import Dict, List, Tuple

from databricks.feature_store.utils.lookup_key_utils import LookupKeyType
from databricks.ml_features_common.entities.data_type import DataType
from databricks.ml_features_common.entities.feature_column_info import FeatureColumnInfo
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
)


class FeatureTableMetadata:
    """
    Encapsulates metadata on a feature table, including lookup keys, feature metadata, and online
    feature table metadata.

    Feature metadata is grouped by lookup key, since different features may require different
    lookup keys (eg pickup_zip and dropoff_zip may each be used to lookup a geographic data feature
    table).
    """

    def __init__(
        self,
        feature_col_infos_by_lookup_key: Dict[
            str, Dict[LookupKeyType, List[FeatureColumnInfo]]
        ],
        online_ft: OnlineFeatureTable,
    ):
        self.feature_col_infos_by_lookup_key = feature_col_infos_by_lookup_key
        self.online_ft = online_ft

    def get_table_feature_type_mapping(self) -> Dict[str, DataType]:
        """
        Returns a mapping from feature name to data type.
        """
        feature_data_type_mapping = {}
        for feature_detail in self.online_ft.features:
            feature_data_type_mapping[feature_detail.name] = feature_detail.data_type
        return feature_data_type_mapping
