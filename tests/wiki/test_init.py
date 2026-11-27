"""
Tests for src.app.wiki.__init__ (fallback logic)
"""

from src import wiki


def test_wiki_init_logic() -> None:

    assert hasattr(wiki, "page")
