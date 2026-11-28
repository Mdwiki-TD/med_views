"""
Tests for database services (revised for corrected schema).
"""

from __future__ import annotations

import pytest

from src.app.database.views_db.services import (
    AggregationService,
    DatabaseService,
    TitleService,
    ViewService,
)


@pytest.fixture
def db_service(tmp_path):
    """Create a temporary database service for testing."""
    db_path = tmp_path / "test.db"
    service = DatabaseService(db_path)
    service.initialize()
    yield service
    DatabaseService.reset_instance()


@pytest.fixture
def title_service(db_service):
    """Create a title service for testing."""
    return TitleService(db_service)


@pytest.fixture
def view_service(db_service):
    """Create a view service for testing."""
    return ViewService(db_service)


@pytest.fixture
def aggregation_service(db_service):
    """Create an aggregation service for testing."""
    return AggregationService(db_service)


class TestTitleService:
    """Tests for TitleService."""

    def test_insert_titles(self, title_service):
        """Test inserting titles."""
        titles = ["Article One", "Article Two", "Article Three"]
        count = title_service.insert_titles("en", titles)
        assert count == 3

    def test_insert_titles_with_underscores(self, title_service):
        """Test inserting titles with underscores (should be normalized)."""
        titles = ["Article_One", "Article_Two"]
        count = title_service.insert_titles("en", titles)
        assert count == 2

        # Verify underscores were replaced
        retrieved = title_service.get_titles_for_language("en")
        assert "Article One" in retrieved
        assert "Article Two" in retrieved

    def test_insert_titles_idempotent(self, title_service):
        """Test that inserting the same titles twice doesn't create duplicates."""
        titles = ["Article One", "Article Two"]

        count1 = title_service.insert_titles("en", titles)
        count2 = title_service.insert_titles("en", titles)

        assert count1 == 2
        # Second insert should not add duplicates (upsert does nothing)
        assert count2 == 0  # No new rows inserted
        total = title_service.get_title_count_for_language("en")
        assert total == 2

    def test_get_titles_for_language(self, title_service):
        """Test retrieving titles for a language."""
        titles = ["Article One", "Article Two", "Article Three"]
        title_service.insert_titles("en", titles)

        retrieved = title_service.get_titles_for_language("en")
        assert len(retrieved) == 3
        assert "Article One" in retrieved

    def test_get_title_count_for_language(self, title_service):
        """Test getting title count for a language."""
        titles = ["Article One", "Article Two"]
        title_service.insert_titles("en", titles)

        count = title_service.get_title_count_for_language("en")
        assert count == 2

    def test_get_all_language_counts(self, title_service):
        """Test getting title counts for all languages."""
        title_service.insert_titles("en", ["Article One", "Article Two"])
        title_service.insert_titles("fr", ["Article Un"])

        counts = title_service.get_all_language_counts()
        assert counts["en"] == 2
        assert counts["fr"] == 1

    def test_delete_titles_for_language(self, title_service):
        """Test deleting titles for a language."""
        titles = ["Article One", "Article Two"]
        title_service.insert_titles("en", titles)

        deleted = title_service.delete_titles_for_language("en")
        assert deleted == 2

        count = title_service.get_title_count_for_language("en")
        assert count == 0

    def test_title_exists(self, title_service):
        """Test checking if a title exists."""
        titles = ["Article One"]
        title_service.insert_titles("en", titles)

        assert title_service.title_exists("en", "Article One") is True
        assert title_service.title_exists("en", "Article Two") is False

    def test_title_exists_normalizes_underscores(self, title_service):
        """Test that title_exists normalizes underscores, matching insert_titles."""
        title_service.insert_titles("en", ["Article_One"])

        # Should find it with underscore form (normalized at query time)
        assert title_service.title_exists("en", "Article_One") is True
        # Should also find it with space form
        assert title_service.title_exists("en", "Article One") is True


class TestViewService:
    """Tests for ViewService."""

    def test_insert_views_all_agents(self, view_service):
        """Test inserting views for all_agents."""
        views_data = {"Article One": 100, "Article Two": 200}
        count = view_service.insert_views("en", 2024, views_data, "all_agents")
        assert count == 2

    def test_insert_views_users_agents(self, view_service):
        """Test inserting views for users_agents."""
        views_data = {"Article One": 100, "Article Two": 200}
        count = view_service.insert_views("en", 2024, views_data, "users_agents")
        assert count == 2

    def test_get_views_for_language_year(self, view_service):
        """Test retrieving views for a language and year."""
        views_data = {"Article One": 100, "Article Two": 200}
        view_service.insert_views("en", 2024, views_data, "all_agents")

        retrieved = view_service.get_views_for_language_year("en", 2024, "all_agents")
        assert retrieved == views_data

    def test_get_total_views_for_language_year(self, view_service):
        """Test getting total views for a language and year."""
        views_data = {"Article One": 100, "Article Two": 200}
        view_service.insert_views("en", 2024, views_data, "all_agents")

        total = view_service.get_total_views_for_language_year("en", 2024, "all_agents")
        assert total == 300

    def test_get_title_count_for_language_year(self, view_service):
        """Test getting title count for a language and year."""
        views_data = {"Article One": 100, "Article Two": 200, "Article Three": 300}
        view_service.insert_views("en", 2024, views_data, "all_agents")

        count = view_service.get_title_count_for_language_year("en", 2024, "all_agents")
        assert count == 3

    def test_delete_views_for_language_year(self, view_service):
        """Test deleting views for a language and year."""
        views_data = {"Article One": 100, "Article Two": 200}
        view_service.insert_views("en", 2024, views_data, "all_agents")

        deleted = view_service.delete_views_for_language_year("en", 2024, "all_agents")
        assert deleted == 2

        total = view_service.get_total_views_for_language_year("en", 2024, "all_agents")
        assert total == 0

    def test_upsert_views(self, view_service):
        """Test that upserting views updates existing records."""
        views_data1 = {"Article One": 100, "Article Two": 200}
        view_service.insert_views("en", 2024, views_data1, "all_agents")

        # Upsert with new values
        views_data2 = {"Article One": 150, "Article Two": 250}
        view_service.insert_views("en", 2024, views_data2, "all_agents")

        # Verify updated values
        retrieved = view_service.get_views_for_language_year("en", 2024, "all_agents")
        assert retrieved["Article One"] == 150
        assert retrieved["Article Two"] == 250


class TestAggregationService:
    """Tests for AggregationService."""

    def test_compute_language_counts(self, view_service, aggregation_service):
        """Test computing language counts."""
        views_data = {"Article One": 100, "Article Two": 200}
        view_service.insert_views("en", 2024, views_data, "all_agents")

        counts = aggregation_service.compute_language_counts("en", 2024, "all_agents")
        assert counts["total_views"] == 300

    def test_cache_language_counts(self, view_service, aggregation_service):
        """Test caching language counts."""
        views_data = {"Article One": 100, "Article Two": 200}
        view_service.insert_views("en", 2024, views_data, "all_agents")

        # Compute and cache
        counts = aggregation_service.compute_language_counts("en", 2024, "all_agents")
        aggregation_service.cache_language_counts("en", 2024, "all_agents", counts["total_views"])

        # Retrieve cached
        cached = aggregation_service.get_cached_language_counts("en", 2024, "all_agents")
        assert cached is not None
        assert cached["total_views"] == 300

    def test_get_all_language_counts_for_year(self, view_service, aggregation_service):
        """Test getting all language counts for a year."""
        view_service.insert_views("en", 2024, {"Article One": 100}, "all_agents")
        view_service.insert_views("fr", 2024, {"Article Un": 200}, "all_agents")

        # Compute and cache
        for lang in ["en", "fr"]:
            counts = aggregation_service.compute_language_counts(lang, 2024, "all_agents")
            aggregation_service.cache_language_counts(lang, 2024, "all_agents", counts["total_views"])

        # Retrieve all
        all_counts = aggregation_service.get_all_language_counts_for_year(2024, "all_agents")
        assert "en" in all_counts
        assert "fr" in all_counts
        assert all_counts["fr"] == 200  # Sorted descending

    def test_cache_statistics(self, aggregation_service):
        """Test caching statistics."""
        aggregation_service.cache_statistics(
            lang="en",
            year=2024,
            articles=100,
            empty_views=20,
            not_empty_views=80,
            hash_count=5,
            total_views=10000,
        )

        cached = aggregation_service.get_cached_statistics("en", 2024)
        assert cached is not None
        assert cached["articles"] == 100
        assert cached["total_views"] == 10000

    def test_cache_statistics_upsert_with_year_zero(self, aggregation_service):
        """Test that year=0 (all-years summary) upserts correctly."""
        aggregation_service.cache_statistics(
            lang="en",
            year=0,
            articles=100,
            empty_views=20,
            not_empty_views=80,
            hash_count=5,
            total_views=10000,
        )
        # Second call should update, not insert a duplicate
        aggregation_service.cache_statistics(
            lang="en",
            year=0,
            articles=200,
            empty_views=40,
            not_empty_views=160,
            hash_count=10,
            total_views=20000,
        )

        cached = aggregation_service.get_cached_statistics("en", 0)
        assert cached is not None
        assert cached["articles"] == 200
        assert cached["total_views"] == 20000


class TestDatabaseService:
    """Tests for DatabaseService."""

    def test_initialize(self, tmp_path):
        """Test database initialization."""
        db_path = tmp_path / "test.db"
        service = DatabaseService(db_path)
        service.initialize()

        assert db_path.exists()
        DatabaseService.reset_instance()

    def test_singleton_pattern(self, tmp_path):
        """Test singleton pattern."""
        db_path = tmp_path / "test.db"

        service1 = DatabaseService.get_instance(db_path)
        service2 = DatabaseService.get_instance()

        assert service1 is service2
        DatabaseService.reset_instance()

    def test_get_session(self, db_service):
        """Test session context manager."""
        with db_service.get_session() as session:
            assert session is not None

    def test_session_rollback_on_error(self, db_service):
        """Test that session rolls back on error."""
        try:
            with db_service.get_session() as session:
                # This will cause an error
                session.execute("INVALID SQL")
        except Exception:
            pass

        # Should be able to get a new session
        with db_service.get_session() as session:
            assert session is not None
