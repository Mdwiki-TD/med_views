"""
Tests for src.app.helps
"""

from src.app.helps import JsonHelper


class TestJsonHelper:
    """Tests for the JsonHelper class."""

    def test_is_empty_data_none(self):
        """Test None data is empty."""
        assert JsonHelper.is_empty_data(None) is True

    def test_is_empty_data_empty_dict(self):
        """Test empty dict is empty."""
        assert JsonHelper.is_empty_data({}) is True

    def test_is_empty_data_zero_all(self):
        """Test dict with all=0 is empty."""
        assert JsonHelper.is_empty_data({"all": 0}) is True

    def test_is_empty_data_single_key(self):
        """Test dict with single key is empty."""
        assert JsonHelper.is_empty_data({"key": "value"}) is True

    def test_is_empty_data_not_empty(self):
        """Test non-empty dict."""
        assert JsonHelper.is_empty_data({"all": 100, "2024": 100}) is False
