"""Pytest configuration and fixtures for tests."""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock
from redis import Redis

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis_mock = Mock(spec=Redis)
    return redis_mock


@pytest.fixture
def real_redis():
    """
    Create a real Redis connection for integration tests.
    Skips test if Redis is not available.
    """
    try:
        r = Redis(host='localhost', port=6379, db=15, decode_responses=False)
        r.ping()
        # Clean up test database
        r.flushdb()
        yield r
        # Clean up after test
        r.flushdb()
        r.close()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        'a': 'hello',
        'b': 'world',
        'c': 'test'
    }


@pytest.fixture
def sample_job_name():
    """Sample Laravel job class name."""
    return 'App\\Jobs\\TestJob'

