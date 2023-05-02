import pytest

# Test inputs from command line
@pytest.parametrize("input", [])
def test_valid_csv(input):
    pass

# parametrize valid, not valid, uneven, weird values in the middle of the matrix (these are not actually tested)
@pytest.parametrize("input", [])
def test_valid_file_input(input):
    pass

# parametrize
@pytest.parametrize("table_size,valid", [
    (0, False),
    (10, True),
    (-9, False),
    (10.2, False),
    ("Not an int", False),
])
def test_valid_table_size(table_size,valid):
    pass

# parametrize
@pytest.parametrize("granularity,valid", [
    ("", True),
    ("0", True),
    ("1", True),
    ("2", True),
    ("3", False),
    ("-1", False),
    ("1.1", False),
    ("Not an int", False),
])
def test_valid_granularity(granularity,valid):
    pass
