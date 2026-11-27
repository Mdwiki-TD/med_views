"""
Tests for src.app.sql_utils
"""

from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch

from src.app.sql_utils import (
    MedicalTitlesRepository,
    get_en_articles,
    one_lang_titles,
    retrieve_medicine_titles,
)


def test_get_en_articles(monkeypatch: MonkeyPatch) -> None:
    mock_repo = MagicMock(spec=MedicalTitlesRepository)
    mock_repo.get_en_articles.return_value = ["Title1", "Title2"]

    monkeypatch.setattr(
        "src.app.sql_utils._get_default_repo",
        lambda: mock_repo,
    )

    result = get_en_articles()
    assert result == ["Title1", "Title2"]


def test_retrieve_medicine_titles(monkeypatch: MonkeyPatch) -> None:
    mock_repo = MagicMock(spec=MedicalTitlesRepository)
    mock_repo.retrieve_medicine_titles.return_value = {
        "en": ["EnTitle1", "EnTitle2"],
        "fr": ["FrTitle1", "FrTitle2"],
        "de": ["DeTitle1"],
    }

    monkeypatch.setattr(
        "src.app.sql_utils._get_default_repo",
        lambda: mock_repo,
    )

    result = retrieve_medicine_titles()

    assert set(result["en"]) == {"EnTitle1", "EnTitle2"}
    assert result["fr"] == ["FrTitle1", "FrTitle2"]
    assert result["de"] == ["DeTitle1"]


def test_one_lang_titles(monkeypatch: MonkeyPatch) -> None:
    mock_repo = MagicMock(spec=MedicalTitlesRepository)
    mock_repo.one_lang_titles.side_effect = lambda lang: ["EnT"] if lang == "en" else ["T1", "T2"]

    monkeypatch.setattr(
        "src.app.sql_utils._get_default_repo",
        lambda: mock_repo,
    )

    # Test for en (delegates to get_en_articles)
    assert one_lang_titles("en") == ["EnT"]

    # Test for other lang
    result = one_lang_titles("fr")
    assert result == ["T1", "T2"]
