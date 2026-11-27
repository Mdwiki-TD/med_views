"""
Tests for src.api_sql.sql_utils
"""

from unittest.mock import MagicMock

from src.app.api_sql.sql_utils import MedicalTitlesRepository


class TestMedicalTitlesRepository:
    """Tests for the MedicalTitlesRepository class."""

    def test_get_en_articles(self):
        mock_sql_client = MagicMock()
        mock_sql_client.retrieve_sql_results.return_value = [
            {"page_title": "Title1"},
            {"page_title": "Title2"},
        ]

        repo = MedicalTitlesRepository(sql_client=mock_sql_client)
        result = repo.get_en_articles()

        assert result == ["Title1", "Title2"]
        mock_sql_client.retrieve_sql_results.assert_called_once()

    def test_retrieve_medicine_titles(self):
        mock_sql_client = MagicMock()
        mock_sql_client.retrieve_sql_results.side_effect = [
            # First call: retrieve_medicine_titles query
            [
                {"page_title": "EnTitle1", "ll_lang": "fr", "ll_title": "FrTitle1"},
                {"page_title": "EnTitle1", "ll_lang": "de", "ll_title": "DeTitle1"},
                {"page_title": "EnTitle2", "ll_lang": "fr", "ll_title": "FrTitle2"},
            ],
            # Second call: get_en_articles query
            [{"page_title": "EnTitle1"}, {"page_title": "EnTitle2"}],
        ]

        repo = MedicalTitlesRepository(sql_client=mock_sql_client)
        result = repo.retrieve_medicine_titles()

        assert set(result["en"]) == {"EnTitle1", "EnTitle2"}
        assert result["fr"] == ["FrTitle1", "FrTitle2"]
        assert result["de"] == ["DeTitle1"]

    def test_one_lang_titles_english(self):
        mock_sql_client = MagicMock()
        mock_sql_client.retrieve_sql_results.return_value = [{"page_title": "EnT"}]

        repo = MedicalTitlesRepository(sql_client=mock_sql_client)
        result = repo.one_lang_titles("en")

        assert result == ["EnT"]

    def test_one_lang_titles_other_language(self):
        mock_sql_client = MagicMock()
        mock_sql_client.retrieve_sql_results.return_value = [
            {"ll_title": "T1"},
            {"ll_title": "T2"},
        ]

        repo = MedicalTitlesRepository(sql_client=mock_sql_client)
        result = repo.one_lang_titles("fr")

        assert result == ["T1", "T2"]
