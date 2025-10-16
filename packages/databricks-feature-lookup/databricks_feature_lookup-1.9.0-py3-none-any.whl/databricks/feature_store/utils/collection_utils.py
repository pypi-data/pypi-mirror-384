"""
Utils for collection classes and functions.
"""

from typing import Any, Dict, List, Tuple


class LookupKeyList:
    """
    Lightweight collection for storing a table of lookup primary keys.
    This is faster than pandas DataFrame for small tables.
    """

    def __init__(self, columns: List[str], rows: List[List[Any]]):
        """
        Note: do not modify the columns or rows.

        :param columns: Ordered list of column names.
        :param rows: A list of rows where each row is a list of values, ordered by the columns.
        """
        self._columns = columns
        self._rows = rows
        self._items = [list(zip(columns, row)) for row in rows]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        """
        :param d: A dictionary mapping column names to lists of values.
        :return: A LookupKeyList instance.
        """
        return cls(columns=list(d.keys()), rows=list(zip(*d.values())))

    @property
    def columns(self) -> List[str]:
        return self._columns

    @property
    def rows(self) -> List[List[Any]]:
        return self._rows

    @property
    def items(self) -> List[List[Tuple[str, Any]]]:
        """
        :return: A list of rows where each row is a list of (column, value) tuples.
        """
        return self._items

    def __eq__(self, other):
        if not isinstance(other, LookupKeyList):
            return False

        return self.columns == other.columns and self.rows == other.rows

    def __repr__(self):
        return f"LookupKeyList(columns={self.columns}, rows={self.rows})"

    def __str__(self):
        return self.__repr__()
