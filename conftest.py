import os
import sys

import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))


# Add any shared fixtures here
@pytest.fixture(scope="session")
def base_url():
    return "http://localhost:8000"
