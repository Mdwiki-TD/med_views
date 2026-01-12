"""
Tests for src.config
"""
import sys
from unittest.mock import patch
import pytest


def test_parallelism_default():
    # Since src.config is already imported, we might need to reload it or mock sys.argv before import.
    # But usually config is imported once at startup.
    # We can test the logic by mocking sys.argv and reloading the module,
    # but that might affect other tests.
    # Alternatively, we can just test that the logic in the file works if it was a function.

    # Let's try to reload it in a controlled environment
    import importlib
    import src.config

    with patch.object(sys, 'argv', ['script.py']):
        importlib.reload(src.config)
        assert src.config.parallelism == 10

    with patch.object(sys, 'argv', ['script.py', '-para:20']):
        importlib.reload(src.config)
        assert src.config.parallelism == 20
