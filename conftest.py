import pytest
from seating_chart import main

@pytest.fixture(scope="function")
def run_program():
    main("guest_matrix.csv")