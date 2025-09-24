# Basic pytest configuration for focused testing
import pytest

@pytest.fixture
def sample_data():
    return {"value": 42, "name": "test"}
