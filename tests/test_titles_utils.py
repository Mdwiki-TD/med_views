"""
Tests for src.app.titles_utils
"""

from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch

from src.app.titles_utils import (
    TitlesLoader,
    load_lang_titles,
)


def test_load_lang_titles(monkeypatch: MonkeyPatch) -> None:
    mock_loader = MagicMock(spec=TitlesLoader)

    # Scenario 1: load_lang_titles returns data from dump
    mock_loader.load_lang_titles.side_effect = lambda lang: ["Title 1", "Title 2"]
    monkeypatch.setattr(
        "src.app.titles_utils._get_default_loader",
        lambda: mock_loader,
    )

    result = load_lang_titles("en")
    assert result == ["Title 1", "Title 2"]
