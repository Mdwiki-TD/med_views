"""
Tests for src.titles_utils
"""
import sys
from unittest.mock import MagicMock

from src.titles_utils import (
    load_lang_titles,
)


def test_load_lang_titles(monkeypatch):
    # Scenario 1: load_lang_titles_from_dump returns data
    mock_dump = MagicMock(return_value=["Title 1", "Title 2"])
    monkeypatch.setattr("src.titles_utils.load_lang_titles_from_dump", mock_dump)

    result = load_lang_titles("en")
    assert result == ["Title 1", "Title 2"]
    mock_dump.assert_called_once_with("en")

    # Scenario 2: load_lang_titles_from_dump returns empty, 'local' in sys.argv
    # We can reuse monkeypatch to set return_value
    mock_dump.return_value = []
    monkeypatch.setattr("sys.argv", ["script.py", "local"])
    result = load_lang_titles("en")
    assert result == []
    mock_dump.assert_called_with("en")

    # Scenario 3: load_lang_titles_from_dump returns empty, 'local' NOT in sys.argv
    mock_dump.return_value = []
    mock_sql = MagicMock(return_value=["Title_1", "Title_2"])
    monkeypatch.setattr("src.titles_utils.one_lang_titles", mock_sql)
    monkeypatch.setattr("sys.argv", ["script.py"])

    result = load_lang_titles("en")

    # Verify underscores are replaced
    assert result == ["Title 1", "Title 2"]
    mock_dump.assert_called_with("en")
    mock_sql.assert_called_once_with("en")
