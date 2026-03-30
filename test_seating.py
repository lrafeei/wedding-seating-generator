import pytest
from argparse import ArgumentTypeError
from seating_chart import argument_parser, csv_file_checker, table_size_checker


def test_valid_csv_file():
    assert "example_matrix.csv" == csv_file_checker("example_matrix.csv")


@pytest.mark.parametrize(
        "csv_file",
        [
            None,
            "non_existent_file.csv",
            "non_csv_file.txt",
            "invalid_csv_formatted_file.csv",
        ],
        ids=[
            "No file provided",
            "Non-existent file",
            "Non-CSV file",
            "Invalid CSV formatted file",
        ],
)
def test_invalid_csv_file(csv_file):
    with pytest.raises(ArgumentTypeError):
        csv_file_checker(csv_file)


@pytest.mark.parametrize("table_size", (4, "4"), ids=["integer", "string of integer"])
def test_valid_table_size(table_size):
    assert 4 == table_size_checker(table_size)


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
    with pytest.raises(ArgumentTypeError):
        table_size_checker(table_size)


def test_table_size_greater_than_guest_count():
    "Seat everyone at one table" == main("example_matrix.csv", 8, None)



