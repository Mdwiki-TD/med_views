"""
Tests for src.sql_utils
"""
import unittest.mock
from unittest.mock import patch

from src.sql_utils import (
    get_en_articles,
    get_language_article_counts_sql,
    one_lang_titles,
    retrieve_medicine_titles,
)


def test_get_en_articles():
    with patch("src.sql_utils.retrieve_sql_results") as mock_sql:
        mock_sql.return_value = [{"page_title": "Title1"}, {"page_title": "Title2"}]
        result = get_en_articles()
        assert result == ["Title1", "Title2"]
        mock_sql.assert_called_once()
        args, _ = mock_sql.call_args
        assert "enwiki" in args


def test_get_language_article_counts_sql():
    with patch("src.sql_utils.retrieve_sql_results") as mock_sql:
        mock_sql.return_value = [
            {"ll_lang": "fr", "counts": 10},
            {"ll_lang": "de", "counts": 5},
            {"ll_lang": "en", "counts": 20},
        ]

        result = get_language_article_counts_sql()

        expected = {"fr": 10, "de": 5, "en": 20}
        assert result == expected
        mock_sql.assert_called_once()


def test_retrieve_medicine_titles():
    with patch("src.sql_utils.retrieve_sql_results") as mock_sql:
        mock_sql.return_value = [
            {"page_title": "EnTitle1", "ll_lang": "fr", "ll_title": "FrTitle1"},
            {"page_title": "EnTitle1", "ll_lang": "de", "ll_title": "DeTitle1"},
            {"page_title": "EnTitle2", "ll_lang": "fr", "ll_title": "FrTitle2"},
        ]

        result = retrieve_medicine_titles()

        assert set(result["en"]) == {"EnTitle1", "EnTitle2"}
        assert result["fr"] == ["FrTitle1", "FrTitle2"]
        assert result["de"] == ["DeTitle1"]
        mock_sql.assert_called_once()


def test_one_lang_titles():
    with patch("src.sql_utils.retrieve_sql_results") as mock_sql:
        mock_sql.return_value = [{"ll_title": "T1"}, {"ll_title": "T2"}]

        # Test for en (delegates to get_en_articles)
        with patch("src.sql_utils.get_en_articles") as mock_en:
            mock_en.return_value = ["EnT"]
            assert one_lang_titles("en") == ["EnT"]

        # Test for other lang
        result = one_lang_titles("fr")
        assert result == ["T1", "T2"]
        mock_sql.assert_called_with(unittest.mock.ANY, "enwiki", values=("fr",))
