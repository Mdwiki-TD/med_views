"""
Tests for src.app.config
"""

import importlib
import sys

from _pytest.monkeypatch import MonkeyPatch


def test_parallelism_default(monkeypatch: MonkeyPatch) -> None:
    import src.app.config

    monkeypatch.setattr(sys, "argv", ["script.py"])
    importlib.reload(src.app.config)
    assert src.app.config.parallelism == 10
