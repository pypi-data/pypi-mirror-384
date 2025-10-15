from csv import DictReader
from pathlib import Path
from typing import Any


def try_int(value: Any) -> int | Any:
    """Convert a value to an integer if possible, otherwise return the value."""
    try:
        return int(value)
    except Exception:
        return value


def try_int_record(record: dict) -> dict:
    """Attempt to convert keys and values in a dictionary to integer."""
    return {try_int(k): try_int(v) for k, v in record.items()}


def _load_csv(path: Path) -> list[dict]:
    """Load a csv file to a list of record dictionaries."""
    with path.open() as csvfile:
        return [try_int_record(record) for record in DictReader(csvfile)]


def _list_to_index(records: list[dict]) -> dict[dict]:
    """Convert a list of records to an index using the first key as index key."""
    keys = tuple(records[0].keys())

    if len(keys) == 1:
        return {
            tuple(record.values())[0]: tuple(record.values())[0] for record in records
        }
    if len(keys) == 2:
        return {tuple(record.values())[0]: record[keys[1]] for record in records}
    else:
        return {tuple(record.values())[0]: record for record in records}


def _tables_index() -> dict[str, Path]:
    """Return a index of available id tables. The keys are the table names in
    lowercase."""
    csv_files = sorted(
        Path(__file__).parent.joinpath("FDevIDs").glob("*.csv"),
        key=lambda x: x.stem.lower(),
    )
    return {f.stem.lower(): f for f in csv_files}
