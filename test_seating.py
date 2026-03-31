import pytest
import logging
import seating_chart
from argparse import ArgumentTypeError

_logger = logging.getLogger(__name__)

def test_valid_csv_file():
    assert "test_files/example_matrix.csv" == seating_chart.csv_file_checker('test_files/example_matrix.csv')


@pytest.mark.parametrize(
        "csv_file",
        [
            None,
            "non_existent_file.csv",
        ],
        ids=[
            "No file provided",
            "Non-existent file",
        ],
)
def test_missing_csv_file(csv_file):
    with pytest.raises(ArgumentTypeError):
        seating_chart.csv_file_checker(csv_file)


@pytest.mark.parametrize(
        "csv_file",
        [
            "test_files/non_csv_file.txt",
            "test_files/invalid_csv_formatted_file.csv",
            "test_files/non_integer_relationship_weight.csv"
        ],
        ids=[
            "Non-CSV file",
            "Invalid CSV formatted file",
            "Non-integer relationship weight",
        ],
)
def test_invalid_csv_file(csv_file):
    with pytest.raises(ValueError):
        seating_chart.main(csv_file, 4, 0)


def test_duplicate_csv_file(caplog, monkeypatch):
    with caplog.at_level(logging.WARNING):
        monkeypatch.setattr(seating_chart, "DEBUG_MODE", True)
        seating_chart.main("test_files/duplicate_data.csv", 4, 0)
        assert "Duplicate in relationship matrix found.  Ignoring one of the two values" in caplog.text


def test_conflicting_csv_file(caplog, monkeypatch):
    with caplog.at_level(logging.WARNING):
        monkeypatch.setattr(seating_chart, "DEBUG_MODE", True)
        seating_chart.main("test_files/conflicting_data.csv", 4, 0)
        assert "Duplicate relationships found with different relationship values. Lalleh's Ex and Lalleh Rafeei have weights -10 and 50.  -10 will be used." in caplog.text


@pytest.mark.parametrize("table_size", (4, "4"), ids=["integer", "string of integer"])
def test_valid_table_size(table_size):
    assert 4 == seating_chart.table_size_checker(table_size)


@pytest.mark.parametrize(
        "table_size",
        (None, 0, -3, 0.5, "four"),
        ids=[
            "No table size provided",
            "table_size==0",
            "Negative table size",
            "Fraction table size",
            "Non-integer table size",
        ],
)
def test_invalid_table_size(table_size):
    with pytest.raises((ArgumentTypeError, TypeError)):
        seating_chart.table_size_checker(table_size)


def test_table_size_greater_than_guest_count():
    "Seat everyone at one table" == seating_chart.main("test_files/example_matrix.csv", 8, None)



