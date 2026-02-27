#!/usr/bin/env python3
"""
🧪 Pytest Configuration
Shared fixtures and configuration for all tests.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add hound_core to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "hound_core"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def isolated_event_loop():
    """Create a fresh event loop for each test function."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
