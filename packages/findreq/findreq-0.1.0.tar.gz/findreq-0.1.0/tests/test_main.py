import pytest
from findreq.main import main

def test_main_runs():
    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised an exception: {e}")
