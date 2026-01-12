"""
Tests for src.wiki.mdwiki_page
"""
import sys
from unittest.mock import MagicMock, patch

import pytest

from src.wiki.mdwiki_page import (
    load_main_api,
    page,
)


@patch("src.wiki.mdwiki_page.all_apis_valid", True)
@patch("src.wiki.mdwiki_page.ALL_APIS")
def test_load_main_api(mock_all_apis):
    result = load_main_api()
    assert result is not None
    # Test caching (lru_cache)
    load_main_api()
    assert mock_all_apis.call_count == 1


@patch("src.wiki.mdwiki_page.load_main_api")
def test_page(mock_load_api):
    mock_api = MagicMock()
    mock_load_api.return_value = mock_api
    mock_main_page = MagicMock()
    mock_api.MainPage.return_value = mock_main_page

    p = page("Test Title")

    # Test get_text
    mock_main_page.get_text.return_value = "content"
    assert p.get_text() == "content"

    # Test exists
    mock_main_page.exists.return_value = True
    assert p.exists() is True

    # Test save (Dry run)
    with patch.object(sys, "argv", ["script.py"]):
        assert p.save("new text", "summary", 0, "minor") is True
        mock_main_page.save.assert_not_called()

    # Test save (Actual run)
    with patch.object(sys, "argv", ["script.py", "save"]):
        mock_main_page.save.return_value = True
        assert p.save("new text", "summary", 0, "minor") is True
        mock_main_page.save.assert_called_once()
