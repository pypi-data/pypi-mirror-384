""" Util functions for handling Delta Sharing models.
"""

from typing import Optional

from databricks.feature_store.entities.feature_functions_for_serving import (
    FeatureFunctionsForServing,
)
from databricks.ml_features_common.entities.feature_spec import FeatureSpec
from databricks.ml_features_common.entities.feature_tables_for_serving import (
    FeatureTablesForServing,
)
from databricks.ml_features_common.utils.uc_utils import HIVE_METASTORE_NAME


def get_catalog_name_override(
    feature_spec: FeatureSpec,
    feature_tables_for_serving: Optional[FeatureTablesForServing],
    feature_functions_for_serving: Optional[FeatureFunctionsForServing],
) -> Optional[str]:
    """
    Find the overriding catalog name by comparing the table and function names between
    feature-spec and the feature tables and feature functions for serving. An override is detected
    when all the catalog names in the _for_serving fields are unified and different from the
    original feature spec. This is used to handle delta-shared model and feature specs.
    :param feature_spec: original feature loaded from feature-spec.yaml
    :param feature_tables_for_serving: loaded feature tables for serving
    :param feature_functions_for_serving: loaded feature functions for serving
    :return: The overriding catalog name. None if catalog name isn't overridden.
    """
    table_names = (
        set()
        if feature_tables_for_serving is None
        else {
            table.feature_table_name
            for table in feature_tables_for_serving.online_feature_tables
        }
    )
    function_names = (
        set()
        if feature_functions_for_serving is None
        else {
            function.full_name
            for function in feature_functions_for_serving.ff_for_serving
        }
    )

    feature_spec_table_names = {table.table_name for table in feature_spec.table_infos}
    feature_spec_udf_names = {udf.udf_name for udf in feature_spec.function_infos}

    def extract_catalog_name(name: str) -> Optional[str]:
        name_sections = name.split(".")
        if len(name_sections) == 3:
            return name_sections[0]
        elif len(name_sections) == 2:
            return HIVE_METASTORE_NAME

    catalog_names = {
        extract_catalog_name(name) for name in table_names.union(function_names)
    }
    feature_spec_catalog_names = {
        extract_catalog_name(name)
        for name in feature_spec_table_names.union(feature_spec_udf_names)
    }

    if len(catalog_names) == 1 and catalog_names != feature_spec_catalog_names:
        return catalog_names.pop()
    return None
