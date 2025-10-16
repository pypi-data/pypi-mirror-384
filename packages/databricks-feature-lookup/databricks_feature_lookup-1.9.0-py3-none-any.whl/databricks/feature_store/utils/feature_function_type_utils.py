from typing import List, Tuple

import pandas as pd
import pyarrow as pa

from databricks.ml_features_common.entities.data_type import DataType

# Derived from the Spark to Arrow data type mapping in runtime.
# https://src.dev.databricks.com/databricks/runtime@78d071a6bb90371c937490f81f50f969ca020450/-/blob/sql/catalyst/src/main/scala/org/apache/spark/sql/util/ArrowUtils.scala?L39:3
BASIC_DATA_TYPE_CONVERTERS = {
    DataType.BOOLEAN: pa.bool_(),
    DataType.SHORT: pa.int16(),
    DataType.INTEGER: pa.int32(),
    DataType.LONG: pa.int64(),
    DataType.FLOAT: pa.float32(),
    DataType.DOUBLE: pa.float64(),
    DataType.STRING: pa.utf8(),  # alias for pa.string()
    DataType.BINARY: pa.binary(),
    DataType.DATE: pa.date32(),  # days since epoch
    DataType.TIMESTAMP: pa.timestamp(
        "ns"
    ),  # nanoseconds, time zone naive (implicit UTC)
}


def _spark_to_pyarrow_schema(spark_schema: List[Tuple[str, DataType]]) -> pa.Schema:
    """
    Converts a Spark schema to pyarrow schema.

    Note: Schemas with complex data types are not currently supported.
    """

    def to_pyarrow_field(col: str, spark_data_type: DataType) -> pa.Field:
        if spark_data_type in BASIC_DATA_TYPE_CONVERTERS:
            pa_data_type = BASIC_DATA_TYPE_CONVERTERS[spark_data_type]
        else:
            raise ValueError(
                f"Found unsupported data type '{DataType.to_string(spark_data_type)}' for column '{col}'."
            )
        return pa.field(col, pa_data_type)

    pa_fields = [to_pyarrow_field(col, data_type) for col, data_type in spark_schema]
    return pa.schema(pa_fields)


def cast_pandas_df(
    df: pd.DataFrame, spark_schema: List[Tuple[str, DataType]]
) -> pd.DataFrame:
    """
    Converts a pandas DataFrame to pyarrow Table for data type casting, then returns the casted DataFrame.

    Code is derived from, and should be kept in sync with Safe Spark Python UDF execution.
    https://src.dev.databricks.com/databricks/runtime@78d071a6bb90371c937490f81f50f969ca020450/-/blob/safespark/udf/py/udfserver/server.py?L204:5
    """
    result_schema = _spark_to_pyarrow_schema(spark_schema)
    # Pyarrow conversion drops the index, so we preserve it.
    index = df.index
    try:
        # Python values are converted to Arrow based on result_schema.
        # This doesn't include type coercion and any type mismatch would result in an ArrowTypeError or ArrowInvalid error.
        # Note: Newer pyarrow versions throw ArrowTypeError here, so ArrowInvalid is not required.
        # We pass `preserve_index=False` above because PyArrow otherwise stores the index as a column.
        casted_table = pa.Table.from_pandas(
            df, schema=result_schema, preserve_index=False
        )
    except (pa.ArrowTypeError, pa.ArrowInvalid):
        # In case of type mismatch, try pa.Table.cast for type coercion.
        # For example, this would allow converting string into numbers.
        casted_table = pa.Table.from_pandas(df, preserve_index=False).cast(
            target_schema=result_schema
        )

    return casted_table.to_pandas().set_index(index)
