"""
Tests for src.config
"""
import importlib
import sys
import unittest.mock


def test_parallelism_default():
    import src.config

    with unittest.mock.patch.object(sys, "argv", ["script.py"]):
        importlib.reload(src.config)
        assert src.config.parallelism == 10

    with unittest.mock.patch.object(sys, "argv", ["script.py", "-para:20"]):
        importlib.reload(src.config)
        assert src.config.parallelism == 20
