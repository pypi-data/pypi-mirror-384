"""Shared test fixtures for agentci-client-config tests."""

import pytest
from agentci.client_config import EvaluationCase


@pytest.fixture
def simple_test_case():
    """Create a basic test case for general use."""
    return EvaluationCase(prompt="Test input prompt", output="Expected test output")
