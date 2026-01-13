"""
Tests for src.dump_utils
"""
import json
from pathlib import Path
from unittest.mock import mock_open, MagicMock

from src.dump_utils import (
    count_languages_in_json,
    dump_languages_counts,
    dump_one,
    load_lang_titles_from_dump,
    load_languages_counts,
)


def test_count_languages_in_json(monkeypatch):
    mock_path = MagicMock()
    monkeypatch.setattr("src.dump_utils.json_titles_path", mock_path)

    file1 = MagicMock(spec=Path)
    file1.stem = "en"
    file2 = MagicMock(spec=Path)
    file2.stem = "ar"
    mock_path.glob.return_value = [file1, file2]

    m = mock_open(read_data='["Art1", "Art2"]')
    monkeypatch.setattr("builtins.open", m)
    result = count_languages_in_json()
    assert result == {"en": 2, "ar": 2}


def test_load_lang_titles_from_dump(monkeypatch):
    mock_path = MagicMock()
    monkeypatch.setattr("src.dump_utils.json_titles_path", mock_path)

    mock_file = MagicMock(spec=Path)
    mock_path.__truediv__.return_value = mock_file
    mock_file.exists.return_value = True

    m = mock_open(read_data='["Art_1", "Art_2"]')
    monkeypatch.setattr("builtins.open", m)
    result = load_lang_titles_from_dump("en")
    assert result == ["Art 1", "Art 2"]


def test_dump_one(monkeypatch):
    mock_file = "test.json"
    data = {"key": "value"}
    m = mock_open()
    monkeypatch.setattr("builtins.open", m)

    dump_one(mock_file, data)
    m.assert_called_once_with(mock_file, "w", encoding="utf-8")
    # Check that json.dump was called
    handle = m()
    written = "".join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written) == data


def test_dump_languages_counts(monkeypatch):
    mock_path = MagicMock()
    monkeypatch.setattr("src.dump_utils.main_dump_path", mock_path)

    mock_dump = MagicMock()
    monkeypatch.setattr("src.dump_utils.dump_one", mock_dump)

    # Should not dump if < 200 items (based on source code)
    dump_languages_counts({"en": 10})
    mock_dump.assert_not_called()

    # Should dump if > 200 items
    large_data = {f"l{i}": i for i in range(205)}
    dump_languages_counts(large_data)
    mock_dump.assert_called_once()


def test_load_languages_counts(monkeypatch):
    mock_path = MagicMock()
    monkeypatch.setattr("src.dump_utils.main_dump_path", mock_path)

    mock_file = MagicMock(spec=Path)
    mock_path.__truediv__.return_value = mock_file
    mock_file.exists.return_value = True

    m = mock_open(read_data='{"en": 100}')
    monkeypatch.setattr("builtins.open", m)
    result = load_languages_counts()
    assert result == {"en": 100}
