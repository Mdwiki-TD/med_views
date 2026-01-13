"""
Tests for src.wiki.__init__ (fallback logic)
"""
import importlib
import sys
from unittest.mock import MagicMock
from _pytest.monkeypatch import MonkeyPatch
import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
def test_wiki_init_logic(monkeypatch: MonkeyPatch) -> None:
    import src.wiki

    mock_exists = MagicMock()
    mock_exists.side_effect = lambda p: p == "I:/core/bots/new/newapi_bot"
    monkeypatch.setattr("os.path.exists", mock_exists)

    monkeypatch.setitem(sys.modules, "newapi", MagicMock())
    importlib.reload(src.wiki)
    assert any("newapi_bot" in p for p in sys.path)

    import src.wiki
    assert hasattr(src.wiki, "page")
