"""
Tests for src.app.titles_loader module.
"""

import json
from unittest.mock import MagicMock, patch

from src.app.titles_loader import TitlesLoader


class TestTitlesLoader:
    """Tests for the TitlesLoader class."""

    def test_init_defaults(self, tmp_path):
        """Test initialization with default values."""
        with patch("src.app.titles_loader.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path
            mock_config.get_instance.return_value.paths.dump_dir_titles_path = tmp_path / "titles"

            loader = TitlesLoader()

            assert loader.local is False
            assert loader.dump_dir_path == tmp_path

    def test_init_with_local(self, tmp_path):
        """Test initialization with local=True."""
        with patch("src.app.titles_loader.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path
            mock_config.get_instance.return_value.paths.dump_dir_titles_path = tmp_path / "titles"

            loader = TitlesLoader(local=True)

            assert loader.local is True

    def test_init_with_custom_paths(self, tmp_path):
        """Test initialization with custom dump_dir_path."""
        custom_path = tmp_path / "custom"
        with patch("src.app.titles_loader.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path
            mock_config.get_instance.return_value.paths.dump_dir_titles_path = tmp_path / "titles"

            loader = TitlesLoader(dump_dir_path=custom_path)

            assert loader.dump_dir_path == custom_path

    def test_start_local_mode(self, tmp_path):
        """Test start() in local mode loads from file."""
        titles_path = tmp_path / "titles"
        titles_path.mkdir()

        # Create the all_languages_titles.json file
        all_links = {"en": ["Article1", "Article2"], "fr": ["Article3"]}
        all_file = tmp_path / "all_languages_titles.json"
        all_file.write_text(json.dumps(all_links))

        mock_dump_manager = MagicMock()
        mock_titles_repo = MagicMock()

        with patch("src.app.titles_loader.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path
            mock_config.get_instance.return_value.paths.dump_dir_titles_path = titles_path

            loader = TitlesLoader(
                dump_manager=mock_dump_manager,
                titles_repo=mock_titles_repo,
                local=True,
                dump_dir_path=tmp_path,
            )
            loader.start()

            # Should not call SQL repo in local mode
            mock_titles_repo.retrieve_medicine_titles.assert_not_called()
            # Should dump files
            assert mock_dump_manager.dump_one.called
            assert mock_dump_manager.dump_list.called

    def test_start_non_local_mode(self, tmp_path):
        """Test start() in non-local mode fetches from SQL."""
        titles_path = tmp_path / "titles"
        titles_path.mkdir()

        all_links = {"en": ["Article1", "Article2"], "fr": ["Article3"]}

        mock_dump_manager = MagicMock()
        mock_titles_repo = MagicMock()
        mock_titles_repo.retrieve_medicine_titles.return_value = all_links

        with patch("src.app.titles_loader.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path
            mock_config.get_instance.return_value.paths.dump_dir_titles_path = titles_path

            loader = TitlesLoader(
                dump_manager=mock_dump_manager,
                titles_repo=mock_titles_repo,
                local=False,
                dump_dir_path=tmp_path,
            )
            loader.start()

            # Should call SQL repo in non-local mode
            mock_titles_repo.retrieve_medicine_titles.assert_called_once()

    def test_start_empty_data(self, tmp_path):
        """Test start() with empty data returns early."""
        titles_path = tmp_path / "titles"
        titles_path.mkdir()

        mock_dump_manager = MagicMock()
        mock_titles_repo = MagicMock()
        mock_titles_repo.retrieve_medicine_titles.return_value = {}

        with patch("src.app.titles_loader.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path
            mock_config.get_instance.return_value.paths.dump_dir_titles_path = titles_path

            loader = TitlesLoader(
                dump_manager=mock_dump_manager,
                titles_repo=mock_titles_repo,
                local=False,
                dump_dir_path=tmp_path,
            )
            loader.start()

            # Should not dump anything with empty data
            mock_dump_manager.dump_one.assert_not_called()

    def test_start_dumps_per_language_files(self, tmp_path):
        """Test start() dumps individual language files."""
        titles_path = tmp_path / "titles"
        titles_path.mkdir()

        all_links = {"en": ["Article1", "Article2"], "fr": ["Article3"]}

        mock_dump_manager = MagicMock()
        mock_titles_repo = MagicMock()
        mock_titles_repo.retrieve_medicine_titles.return_value = all_links

        with patch("src.app.titles_loader.Config") as mock_config:
            mock_config.get_instance.return_value.paths.dump_dir_path = tmp_path
            mock_config.get_instance.return_value.paths.dump_dir_titles_path = titles_path

            loader = TitlesLoader(
                dump_manager=mock_dump_manager,
                titles_repo=mock_titles_repo,
                local=False,
                dump_dir_path=tmp_path,
            )
            loader.start()

            # Should dump for each language
            assert mock_dump_manager.dump_list.call_count == 2
