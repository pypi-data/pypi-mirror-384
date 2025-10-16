import base64
import calendar
import json
from abc import abstractmethod
from datetime import date
from decimal import Context, Decimal
from typing import Union

import numpy as np
import pandas as pd

from databricks.feature_store.utils.data_type_details_utils import (
    ELEMENT_TYPE,
    KEY_TYPE,
    VALUE_TYPE,
    get_data_type_from_details,
    parse_decimal_details,
)
from databricks.ml_features_common.utils.converter_utils import (
    Converter,
    return_if_nan,
    return_if_none,
)

"""
This file defines various type converters used across different online stores for online lookup. 
Each online store specifies a set of type converters through constructing a ConverterFactory instance.
Each type converter inherits either a stateless or stateful converter with the same two functions:

to_online_store(value)
# This function is used to convert a feature value in pandas df type to python native type 
# that can be understood by the underlying online store python SDK for primary key lookup.
# This function only needs to be implemented for data types that's supported as a valid primary key data type.

to_pandas(value)
# This function is used to convert a feature value in python native type to pandas df type. 
# This pandas df will then be used for model inference. The expected return type must match 
# the pyspark df -> pandas df conversion for the given data type to avoid training/scoring skew.
"""


class PandasStatelessConverter(Converter):
    @staticmethod
    @abstractmethod
    def to_online_store(value):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def to_pandas(value):
        raise NotImplementedError


class PandasStatefulConverter(Converter):
    def __init__(self, details, get_converter_detailed):
        self._details = details
        self._get_converter_detailed = get_converter_detailed

    @abstractmethod
    def to_online_store(self, value):
        raise NotImplementedError

    @abstractmethod
    def to_pandas(self, value):
        raise NotImplementedError


class PandasIdentityConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value):
        return value

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value):
        return value


# Basic DataType Converters


# Boolean
class PandasBooleanTypeConverter(PandasIdentityConverter):
    pass


class PandasNumericBooleanConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: bool) -> int:
        return int(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: Union[int, Decimal]) -> bool:
        if value != 0 and value != 1:
            raise ValueError("Unsupported value for bool: " + str(value))
        return bool(value)


class PandasBitBooleanConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: bool) -> int:
        return int(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: str) -> bool:
        if ord(value) != 0 and ord(value) != 1:
            raise ValueError("Unsupported value for bool: " + str(value))
        return bool(ord(value))


class PandasObjectBooleanConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: bool) -> bool:
        return value

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: object) -> bool:
        return str(value) in ("True", "true")


# Binary
class PandasBinaryTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value) -> bytearray:
        return bytearray(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    # TODO value is boto3 object
    def to_pandas(value):
        return bytearray(value.value)


class PandasBase64BinaryTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: bytearray) -> str:
        return str(base64.b64encode(value), "utf-8")

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: str) -> bytearray:
        return bytearray(base64.b64decode(value))


# Short
class PandasShortTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: np.int16) -> int:
        return int(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: Union[int, Decimal]) -> np.int16:
        # TODO (ML-20967): We currently return an np.int16 with best effort if there are no undefined values.
        #  However, if a np.nan is provided, we will return np.nan which is a float instead.
        return np.int16(value)


# Integer
class PandasIntTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: np.int32) -> int:
        return int(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: Union[int, Decimal]) -> np.int32:
        # TODO (ML-20967): We currently return an np.int32 with best effort if there are no undefined values.
        #  However, if a np.nan is provided, we will return np.nan which is a float instead.
        return np.int32(value)


# Long
class PandasLongTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: np.int64) -> int:
        return int(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: Union[int, Decimal]) -> np.int64:
        # TODO (ML-20967): We currently return an np.int64 with best effort if there are no undefined values.
        #  However, if a np.nan is provided, we will return np.nan which is a float instead.
        return np.int64(value)


class PandasStringLongTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: np.int64) -> str:
        return str(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: str) -> np.int64:
        # Brickstore HTTP gateway returns Longs as strings.
        return np.int64(value)


# String
class PandasStringTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: str) -> str:
        return str(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: str) -> str:
        return value


# Float
class PandasFloatTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: np.float32) -> float:
        return float(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: Union[float, Decimal]) -> np.float32:
        return np.float32(value)


# Double
class PandasDoubleTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: np.float64) -> float:
        return float(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: Union[float, Decimal]) -> np.float64:
        return np.float64(value)


# Timestamp
# Us -> microseconds precision
class PandasEpochTimestampTypeUsConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: str) -> int:
        # TODO (ML-24922): Investigate if the value type is str or pd.Timestamp
        dt = pd.Timestamp(value).floor("us")
        return int(dt.timestamp() * 1e6)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: int) -> pd.Timestamp:
        return pd.Timestamp(int(value), unit="us")


class PandasIsoTimestampHttpTypeUsConverter(PandasStatelessConverter):
    """
    PandasIsoTimestampHttpTypeUsConverter converts the timestamp type to the ISO-8601 format that is used in Brickstore
    HTTP requests/response.
    """

    # to_online_store should always convert the timestamp from the user's request to a UTC instant accepted by
    # Brickstore API (e.g. '2011-12-03T10:15:30Z'), regardless of whether the user input timestamp:
    #  - contains UTC or other timezone information.
    #  - does not contain any timezone information.
    @staticmethod
    def to_online_store(value: str) -> str:
        """
        to_online_store should always convert the timestamp from the user's request to a UTC instant compatibel with the
        Brickstore API, while preserving the original timezone information. Examples:
        - Timestamp without timezone: '2011-12-03T10:15:30' -> '2011-12-03T10:15:30Z' (automatically converted to UTC)
        - Timestamp with UTC timezone: '2011-12-03T10:15:30Z' -> '2011-12-03T10:15:30Z'
        - Timestamp with a different timezone: '2011-12-03T10:15:30+01:00' -> '2011-12-03T09:15:30Z'
        """
        dt = pd.Timestamp(value, tz="UTC").floor("us").to_pydatetime()
        # dt.isoformat() guarantees the output always ends with '+00:00'. We replace it with 'Z' to match the Brickstore API format.
        return dt.isoformat().replace("+00:00", "") + "Z"

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: str) -> pd.Timestamp:
        """
        to_pandas applied to two types of timestamps:
        - timestamp in the user's request
        - timestamp in the response from Brickstore API.
        to_pandas should always convert the timestamp to a naive timezone timestamp.
        """
        # TODO(ML-37164): Input to this function could be datetime64 due to scoring server
        # converting input dfs to the types specified in signature.
        # Ensure returned as datetime64[ns], not datetime64[ns, UTC]
        return pd.Timestamp(value, tz="UTC").floor("us").replace(tzinfo=None)


class PandasIsoTimestampTypeUsConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: str) -> str:
        # Pandas (<1.4) Timestamp doesn't support timespec to force microsecond output, which is required for lookup.
        # e.g. pd.Timestamp("2022-06-20T15:30:45.000000").isoformat() outputs '2022-06-20T15:30:45'
        # TODO (ML-24922): Investigate if the value type is str or pd.Timestamp.
        #  Also, consider using native pd.Timestamp.isoformat with timespec when feasible.
        dt = pd.Timestamp(value).floor("us").to_pydatetime()
        return dt.isoformat(timespec="microseconds")

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: str) -> pd.Timestamp:
        return pd.Timestamp(value).floor("us")


# Date
class PandasEpochDateTypeConverter(PandasStatelessConverter):
    """
    This converter will allow but truncate all inexact dates to the most recent date.
    """

    @staticmethod
    def to_online_store(value: str) -> int:
        dt = pd.Timestamp(value).date()
        return calendar.timegm(dt.timetuple())

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: int) -> date:
        return pd.Timestamp(int(value), unit="s").date()


class PandasIsoDateTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: str) -> str:
        return pd.Timestamp(value).date().isoformat()

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: str) -> date:
        return pd.Timestamp(value).date()


# Complex DataType Converters
# Decimal
class PandasDecimalTypeConverter(PandasStatefulConverter):
    def __init__(self, details, get_converter_detailed):
        super().__init__(details, get_converter_detailed)
        precision, _ = parse_decimal_details(details)
        self._precision = precision

    def to_online_store(self, value):
        raise NotImplementedError

    @return_if_none
    @return_if_nan
    def to_pandas(self, value: Decimal) -> Decimal:
        # Set the Decimal context with the appropriate precision
        context = Context(prec=self._precision)
        return context.create_decimal(value)


class PandasStringDecimalTypeConverter(PandasStatelessConverter):
    @staticmethod
    def to_online_store(value: Decimal) -> str:
        return str(value)

    @staticmethod
    @return_if_none
    @return_if_nan
    def to_pandas(value: str) -> Decimal:
        return Decimal(value)


# Array
class PandasArrayTypeConverter(PandasStatefulConverter):
    def __init__(self, details, get_converter_detailed):
        super().__init__(details, get_converter_detailed)
        element_data_type_details = details.get(ELEMENT_TYPE)
        element_data_type = get_data_type_from_details(element_data_type_details)
        element_converter = get_converter_detailed(
            element_data_type, details=element_data_type_details
        )
        self._element_converter = element_converter

    def to_online_store(self, value: np.ndarray):
        raise NotImplementedError

    @return_if_none
    @return_if_nan
    def to_pandas(self, value: list) -> np.ndarray:
        return np.array(
            [
                self._element_converter.to_pandas(x) if x is not None else x
                for x in value
            ]
        )


class PandasStringArrayTypeConverter(PandasStatefulConverter):
    def __init__(self, details, get_converter_detailed):
        super().__init__(details, get_converter_detailed)

    def to_online_store(self, value: dict):
        raise NotImplementedError

    @return_if_none
    @return_if_nan
    def to_pandas(self, value: str) -> dict:
        return json.loads(value)


# Map
class PandasMapTypeConverter(PandasStatefulConverter):
    def __init__(self, details, get_converter_detailed):
        super().__init__(details, get_converter_detailed)
        key_data_type_details = details.get(KEY_TYPE)
        key_data_type = get_data_type_from_details(key_data_type_details)
        value_data_type_details = details.get(VALUE_TYPE)
        value_data_type = get_data_type_from_details(value_data_type_details)
        key_converter = get_converter_detailed(
            key_data_type, details=key_data_type_details
        )
        value_converter = get_converter_detailed(
            value_data_type, details=value_data_type_details
        )
        self._key_converter = key_converter
        self._value_converter = value_converter

    def to_online_store(self, value: dict):
        raise NotImplementedError

    @return_if_none
    @return_if_nan
    def to_pandas(self, value: dict) -> dict:
        return {
            self._key_converter.to_pandas(k): (
                self._value_converter.to_pandas(v) if v is not None else v
            )
            for k, v in value.items()
        }


class PandasStringMapTypeConverter(PandasStatefulConverter):
    def __init__(self, details, get_converter_detailed):
        super().__init__(details, get_converter_detailed)

    def to_online_store(self, value: dict):
        raise NotImplementedError

    @return_if_none
    @return_if_nan
    def to_pandas(self, value: str) -> dict:
        return json.loads(value)
