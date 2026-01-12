"""
Tests for src.wiki.mdwiki_page_mwclient
"""
from unittest.mock import patch, MagicMock
import pytest
import mwclient

from src.wiki.mdwiki_page_mwclient import (
    page_mwclient,
)


@patch("mwclient.Site")
def test_page_mwclient(mock_site_class):
    mock_site = MagicMock()
    mock_site_class.return_value = mock_site
    mock_page = MagicMock()
    mock_site.pages.__getitem__.return_value = mock_page

    p = page_mwclient("Test Title")

    # Test get_text
    mock_page.text.return_value = "content"
    assert p.get_text() == "content"

    # Test exists
    mock_page.exists = True
    assert p.exists() is True

    # Test save
    p.save("new text", "summary")
    mock_page.save.assert_called_once_with("new text", summary="summary", minor=False)

    # Test create
    p.create("created text", "created summary")
    assert mock_page.save.call_count == 2
