"""
Test: Extra

Version: 5.12.0
Date updated: 17/10/2025 (dd/mm/yyyy)
"""

# Library
# ---------------------------------------------------------------------------
import pytest

from absfuyu import extra as ext


def test_ext_load():
    assert ext.is_loaded() is True
