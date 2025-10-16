""" Defines the type conversion classes from pandas to dynamodb and vice versa.
"""

from databricks.feature_store.utils.pandas_type_utils import (
    PandasArrayTypeConverter,
    PandasBinaryTypeConverter,
    PandasDecimalTypeConverter,
    PandasDoubleTypeConverter,
    PandasEpochDateTypeConverter,
    PandasEpochTimestampTypeUsConverter,
    PandasFloatTypeConverter,
    PandasIntTypeConverter,
    PandasLongTypeConverter,
    PandasMapTypeConverter,
    PandasNumericBooleanConverter,
    PandasShortTypeConverter,
    PandasStringTypeConverter,
)
from databricks.ml_features_common.entities.data_type import DataType
from databricks.ml_features_common.utils.converter_utils import ConverterFactory

"""
All supported converters.
See the link below for relevant design decision on DynamoDB type conversion.
https://docs.google.com/document/d/1CvdYWUDqEsv69YVv1S9Co2vx-akEaki3v_H3Q2ZMDmo/edit#bookmark=id.qdunvvvuke0e
"""
BASIC_DATA_TYPE_CONVERTERS = {
    DataType.SHORT: PandasShortTypeConverter,
    DataType.INTEGER: PandasIntTypeConverter,
    DataType.LONG: PandasLongTypeConverter,
    DataType.FLOAT: PandasFloatTypeConverter,
    DataType.DOUBLE: PandasDoubleTypeConverter,
    DataType.BOOLEAN: PandasNumericBooleanConverter,
    DataType.STRING: PandasStringTypeConverter,
    DataType.TIMESTAMP: PandasEpochTimestampTypeUsConverter,
    DataType.DATE: PandasEpochDateTypeConverter,
    DataType.BINARY: PandasBinaryTypeConverter,
}

COMPLEX_DATA_TYPE_CONVERTERS = {
    DataType.DECIMAL: PandasDecimalTypeConverter,
    DataType.ARRAY: PandasArrayTypeConverter,
    DataType.MAP: PandasMapTypeConverter,
}

DYNAMODB_DATA_TYPE_CONVERTER_FACTORY = ConverterFactory(
    BASIC_DATA_TYPE_CONVERTERS, COMPLEX_DATA_TYPE_CONVERTERS
)
