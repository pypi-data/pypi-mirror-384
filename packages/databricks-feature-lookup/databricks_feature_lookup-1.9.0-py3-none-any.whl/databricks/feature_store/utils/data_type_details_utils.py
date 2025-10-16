import re

from databricks.ml_features_common.entities.data_type import DataType

ELEMENT_TYPE = "elementType"
KEY_TYPE = "keyType"
VALUE_TYPE = "valueType"


def get_data_type_from_details(details):
    if isinstance(details, str):
        return DataType.from_string(details)
    return DataType.from_string(details.get("type"))


def parse_decimal_details(details):
    """
    Parse Spark's DecimalType JSON representation for precision and scale.

    :param details: DecimalType JSON representation e.g. "decimal(5,3)" has precision 5 and scale 3.
    """
    match = re.search("^decimal\((\d+),(\d+)\)$", details)
    if match is None:
        raise Exception(f"Malformed decimal data type details {details}")

    return int(match.group(1)), int(match.group(2))
