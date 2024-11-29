import asyncio
import os
import sys
from typing import Generator

import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))


# Add any shared fixtures here
@pytest.fixture(scope="session")
def base_url() -> str:
    """Return base URL for API tests."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
