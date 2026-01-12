"""
Tests for src.config
"""
import importlib
import sys


def test_parallelism_default(monkeypatch):
    import src.config

    monkeypatch.setattr(sys, "argv", ["script.py"])
    importlib.reload(src.config)
    assert src.config.parallelism == 10

    monkeypatch.setattr(sys, "argv", ["script.py", "-para:20"])
    importlib.reload(src.config)
    assert src.config.parallelism == 20
