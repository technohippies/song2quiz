import os
import pytest
from dotenv import load_dotenv
from prefect.testing.utilities import prefect_test_harness

# Configure default asyncio settings
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    with prefect_test_harness():
        yield 

def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    # Configure asyncio loop scope
    config.option.asyncio_mode = "strict"

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables for tests"""
    load_dotenv()
    # Debug print
    if os.getenv('OPENROUTER_API_KEY'):
        print("OpenRouter API key found in environment")
    else:
        print("WARNING: No OpenRouter API key found in environment")

def pytest_runtest_setup(item):
    """Skip integration tests if OPENROUTER_API_KEY is not set"""
    if "integration" in item.keywords and not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")