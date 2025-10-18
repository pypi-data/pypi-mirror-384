"""
Global fixture

Version: 5.12.0
Date updated: 17/10/2025 (dd/mm/yyyy)
"""

import pytest


@pytest.fixture(scope="session")
def test_fixture_session():
    """This cache the fixture for current test session"""
    return None
