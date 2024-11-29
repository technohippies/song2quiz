import asyncio
import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import Mock

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from dotenv import load_dotenv
from prefect.testing.utilities import prefect_test_harness

# Add src directory to Python path
src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(src_dir))

# Configure default asyncio settings
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture() -> Generator[None, None, None]:
    with prefect_test_harness():
        yield


def pytest_configure(config: Config) -> None:
    """Configure custom markers"""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    # Configure asyncio loop scope
    config.option.asyncio_mode = "strict"


@pytest.fixture(scope="session", autouse=True)
def load_env() -> None:
    """Load environment variables for tests"""
    load_dotenv()
    # Debug print
    if os.getenv("OPENROUTER_API_KEY"):
        print("OpenRouter API key found in environment")
    else:
        print("WARNING: No OpenRouter API key found in environment")


def pytest_runtest_setup(item: Item) -> None:
    """Skip integration tests if OPENROUTER_API_KEY is not set"""
    if "integration" in item.keywords and not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")


@pytest.fixture
def mock_genius(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock Genius API responses"""
    mock = Mock()
    mock.return_value = {"id": 1234, "song_path": "data/songs/1234"}
    monkeypatch.setattr("src.services.genius.GeniusAPI.search_song", mock)
    return mock


@pytest.fixture
def mock_openrouter(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock OpenRouter API responses"""
    mock = Mock()
    monkeypatch.setattr("src.services.openrouter.OpenRouterClient.complete", mock)
    return mock
