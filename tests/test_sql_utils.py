"""
Tests for src.sql_utils
"""
from unittest.mock import MagicMock, ANY

from src.sql_utils import (
    get_en_articles,
    one_lang_titles,
    retrieve_medicine_titles,
)


def test_get_en_articles(monkeypatch):
    mock_sql = MagicMock(return_value=[{"page_title": "Title1"}, {"page_title": "Title2"}])
    monkeypatch.setattr("src.sql_utils.retrieve_sql_results", mock_sql)

    result = get_en_articles()
    assert result == ["Title1", "Title2"]
    mock_sql.assert_called_once()
    args, _ = mock_sql.call_args
    assert "enwiki" in args


def test_retrieve_medicine_titles(monkeypatch):
    mock_sql = MagicMock(return_value=[
        {"page_title": "EnTitle1", "ll_lang": "fr", "ll_title": "FrTitle1"},
        {"page_title": "EnTitle1", "ll_lang": "de", "ll_title": "DeTitle1"},
        {"page_title": "EnTitle2", "ll_lang": "fr", "ll_title": "FrTitle2"},
    ])
    monkeypatch.setattr("src.sql_utils.retrieve_sql_results", mock_sql)

    result = retrieve_medicine_titles()

    assert set(result["en"]) == {"EnTitle1", "EnTitle2"}
    assert result["fr"] == ["FrTitle1", "FrTitle2"]
    assert result["de"] == ["DeTitle1"]
    mock_sql.assert_called_once()


def test_one_lang_titles(monkeypatch):
    mock_sql = MagicMock(return_value=[{"ll_title": "T1"}, {"ll_title": "T2"}])
    monkeypatch.setattr("src.sql_utils.retrieve_sql_results", mock_sql)

    # Test for en (delegates to get_en_articles)
    mock_en = MagicMock(return_value=["EnT"])
    monkeypatch.setattr("src.sql_utils.get_en_articles", mock_en)
    assert one_lang_titles("en") == ["EnT"]

    # Test for other lang
    result = one_lang_titles("fr")
    assert result == ["T1", "T2"]
    mock_sql.assert_called_with(ANY, "enwiki", values=("fr",))
