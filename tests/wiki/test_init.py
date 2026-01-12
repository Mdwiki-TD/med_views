"""
Tests for src.wiki.__init__ (fallback logic)
"""
import importlib
import sys
from unittest.mock import MagicMock, patch


def test_wiki_init_logic(monkeypatch):
    import src.wiki

    with patch("os.path.exists") as mock_exists:
        # Case 1: newapi exists
        mock_exists.side_effect = lambda p: p == "I:/core/bots/new/newapi_bot"

        with patch.dict(sys.modules, {"newapi": MagicMock()}):
            importlib.reload(src.wiki)
            assert any("newapi_bot" in p for p in sys.path)

    import src.wiki

    assert hasattr(src.wiki, "page")
