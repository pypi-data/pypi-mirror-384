""" Defines the type conversion classes for brickstore HTTP input JSONs and responses.
"""

from databricks.feature_store.utils.pandas_type_utils import (
    PandasArrayTypeConverter,
    PandasBase64BinaryTypeConverter,
    PandasDoubleTypeConverter,
    PandasFloatTypeConverter,
    PandasIntTypeConverter,
    PandasIsoDateTypeConverter,
    PandasIsoTimestampHttpTypeUsConverter,
    PandasMapTypeConverter,
    PandasObjectBooleanConverter,
    PandasShortTypeConverter,
    PandasStringDecimalTypeConverter,
    PandasStringLongTypeConverter,
    PandasStringTypeConverter,
)
from databricks.ml_features_common.entities.data_type import DataType
from databricks.ml_features_common.utils.converter_utils import ConverterFactory

"""
All supported converters.
"""
BASIC_DATA_TYPE_CONVERTERS = {
    DataType.SHORT: PandasShortTypeConverter,
    DataType.INTEGER: PandasIntTypeConverter,
    DataType.LONG: PandasStringLongTypeConverter,
    DataType.FLOAT: PandasFloatTypeConverter,
    DataType.DOUBLE: PandasDoubleTypeConverter,
    DataType.BOOLEAN: PandasObjectBooleanConverter,
    DataType.STRING: PandasStringTypeConverter,
    DataType.TIMESTAMP: PandasIsoTimestampHttpTypeUsConverter,
    DataType.DATE: PandasIsoDateTypeConverter,
    DataType.BINARY: PandasBase64BinaryTypeConverter,
    DataType.DECIMAL: PandasStringDecimalTypeConverter,
}

COMPLEX_DATA_TYPE_CONVERTERS = {
    DataType.ARRAY: PandasArrayTypeConverter,
    DataType.MAP: PandasMapTypeConverter,
}

BRICKSTORE_HTTP_DATA_TYPE_CONVERTER_FACTORY = ConverterFactory(
    BASIC_DATA_TYPE_CONVERTERS, COMPLEX_DATA_TYPE_CONVERTERS
)
