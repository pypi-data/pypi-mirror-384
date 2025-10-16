""" Defines the type conversion classes from pandas to SQL and vice versa.
"""

from databricks.feature_store.utils.pandas_type_utils import (
    PandasBitBooleanConverter,
    PandasDecimalTypeConverter,
    PandasIdentityConverter,
    PandasStringArrayTypeConverter,
    PandasStringMapTypeConverter,
)
from databricks.ml_features_common.entities.data_type import DataType
from databricks.ml_features_common.utils.converter_utils import ConverterFactory

"""
All supported converters.
"""
BASIC_DATA_TYPE_CONVERTERS = {
    DataType.SHORT: PandasIdentityConverter,
    DataType.INTEGER: PandasIdentityConverter,
    DataType.LONG: PandasIdentityConverter,
    DataType.FLOAT: PandasIdentityConverter,
    DataType.DOUBLE: PandasIdentityConverter,
    DataType.BOOLEAN: PandasBitBooleanConverter,
    DataType.STRING: PandasIdentityConverter,
    DataType.TIMESTAMP: PandasIdentityConverter,
    DataType.DATE: PandasIdentityConverter,
    DataType.BINARY: PandasIdentityConverter,
}

COMPLEX_DATA_TYPE_CONVERTERS = {
    DataType.DECIMAL: PandasDecimalTypeConverter,
    DataType.ARRAY: PandasStringArrayTypeConverter,
    DataType.MAP: PandasStringMapTypeConverter,
}

SQL_DATA_TYPE_CONVERTER_FACTORY = ConverterFactory(
    BASIC_DATA_TYPE_CONVERTERS, COMPLEX_DATA_TYPE_CONVERTERS
)
