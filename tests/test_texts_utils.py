"""
Tests for src.app.texts_utils
"""

from src.app.texts_utils import WikiTextBuilder


class TestWikiTextBuilder:
    """Tests for the WikiTextBuilder class."""

    def test_build_wiki_text_basic(self):
        """Test building basic wiki text."""
        builder = WikiTextBuilder()
        languages = {"en": 100, "ar": 50}
        views = {"en": 10000, "ar": 5000}

        result = builder.build_wiki_text(languages, views)

        assert "Total views for medical content = 15,000" in result
        assert "Total articles= 150" in result
        assert "en" in result
        assert "ar" in result

    def test_build_wiki_text_empty(self):
        """Test building wiki text with empty data."""
        builder = WikiTextBuilder()
        result = builder.build_wiki_text({}, {})

        assert "Total views for medical content = 0" in result
        assert "Total articles= 0" in result

    def test_build_wiki_text_sorted_by_count(self):
        """Test that languages are sorted by article count."""
        builder = WikiTextBuilder()
        languages = {"en": 100, "fr": 200, "de": 50}
        views = {"en": 1000, "fr": 2000, "de": 500}

        result = builder.build_wiki_text(languages, views)

        # fr should appear before en, en before de
        fr_pos = result.find("fr")
        en_pos = result.find("en")
        de_pos = result.find("de")

        assert fr_pos < en_pos < de_pos

    def test_build_wiki_text_average_views(self):
        """Test average views calculation."""
        builder = WikiTextBuilder()
        languages = {"en": 100}
        views = {"en": 1500}

        result = builder.build_wiki_text(languages, views)

        # Average should be 1500 // 100 = 15
        assert "15" in result
