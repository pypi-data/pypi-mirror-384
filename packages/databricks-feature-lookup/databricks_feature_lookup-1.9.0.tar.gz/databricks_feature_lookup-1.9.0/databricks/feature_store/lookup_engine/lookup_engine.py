""" Defines the LookupEngine class, which is used to perform lookups on online stores. This class
differs from Publish in that its actions are read-only.
"""

import abc
import collections
import functools
import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from databricks.feature_store.utils.collection_utils import LookupKeyList
from databricks.feature_store.utils.metrics_utils import LookupClientMetrics
from databricks.ml_features_common.entities.online_feature_table import (
    OnlineFeatureTable,
)
from databricks.ml_features_common.entities.online_store_for_serving import (
    MySqlConf,
    SqlServerConf,
)

LookupKeyType = Tuple[str, ...]


class LookupEngine(abc.ABC):
    @abc.abstractmethod
    def lookup_features(
        self,
        lookup_list: LookupKeyList,
        feature_names: List[str],
        *,
        metrics: LookupClientMetrics = None,
    ) -> pd.DataFrame:
        raise NotImplementedError

    @abc.abstractmethod
    def batch_lookup_features(
        self,
        lookup_list_dict: Dict[str, Dict[LookupKeyType, LookupKeyList]],
        feature_names_dict: Dict[str, Dict[LookupKeyType, List[str]]],
        *,
        metrics: LookupClientMetrics = None,
    ) -> Dict[str, Dict[LookupKeyType, pd.DataFrame]]:
        raise NotImplementedError

    @abc.abstractmethod
    def shutdown(self) -> None:
        raise NotImplementedError
