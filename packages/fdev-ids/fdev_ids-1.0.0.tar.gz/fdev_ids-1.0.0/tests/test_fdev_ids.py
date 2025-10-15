from typing import get_args

import pytest

from fdev_ids import load_table
from fdev_ids import TableName
from fdev_ids import tables
from fdev_ids._loader import _tables_index


@pytest.mark.parametrize("table", tuple(_tables_index().keys()))
def test_load_table(data_regression, table):
    """Verify that all csv files can be loaded as a table and verify the data in each
    table."""
    data_regression.check(load_table(table))


def test_all_tables_in_literal():
    """Verify that all csv files in FDevIDs are included in the TableName Literal."""
    assert get_args(TableName) == tuple(_tables_index().keys())


def test_tables():
    """Verify that the `tables` module variable includes all avaliable tables."""
    assert tables == tuple(_tables_index().keys())
