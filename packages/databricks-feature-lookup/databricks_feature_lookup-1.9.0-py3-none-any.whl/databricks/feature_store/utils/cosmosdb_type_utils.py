""" Defines the type conversion classes from pandas to cosmosdb and vice versa.
"""

from databricks.feature_store.utils.pandas_type_utils import (
    PandasArrayTypeConverter,
    PandasBase64BinaryTypeConverter,
    PandasBooleanTypeConverter,
    PandasDecimalTypeConverter,
    PandasDoubleTypeConverter,
    PandasFloatTypeConverter,
    PandasIntTypeConverter,
    PandasIsoDateTypeConverter,
    PandasIsoTimestampTypeUsConverter,
    PandasLongTypeConverter,
    PandasMapTypeConverter,
    PandasShortTypeConverter,
    PandasStringTypeConverter,
)
from databricks.ml_features_common.entities.data_type import DataType
from databricks.ml_features_common.utils.converter_utils import ConverterFactory

"""
All supported converters.
See the link below for relevant design decision on Cosmos DB type conversion.
https://docs.google.com/document/d/1cG7PDWHld-WwD2UWp7v80KJT7lXOvvO0wNyKuZG2VQ8/edit#heading=h.24cgj83368tv
"""
BASIC_DATA_TYPE_CONVERTERS = {
    DataType.SHORT: PandasShortTypeConverter,
    DataType.INTEGER: PandasIntTypeConverter,
    DataType.LONG: PandasLongTypeConverter,
    DataType.FLOAT: PandasFloatTypeConverter,
    DataType.DOUBLE: PandasDoubleTypeConverter,
    DataType.BOOLEAN: PandasBooleanTypeConverter,
    DataType.STRING: PandasStringTypeConverter,
    DataType.TIMESTAMP: PandasIsoTimestampTypeUsConverter,
    DataType.DATE: PandasIsoDateTypeConverter,
    DataType.BINARY: PandasBase64BinaryTypeConverter,
}

COMPLEX_DATA_TYPE_CONVERTERS = {
    DataType.DECIMAL: PandasDecimalTypeConverter,
    DataType.ARRAY: PandasArrayTypeConverter,
    DataType.MAP: PandasMapTypeConverter,
}

COSMOSDB_DATA_TYPE_CONVERTER_FACTORY = ConverterFactory(
    BASIC_DATA_TYPE_CONVERTERS, COMPLEX_DATA_TYPE_CONVERTERS
)
