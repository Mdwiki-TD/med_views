"""
Tests
# TODO: Implement test
"""
import pytest

from src.services.mw_views import (
    PageviewsClient,
)


@pytest.mark.network
def test_PageviewsClient():
    # TODO: Implement test
    view_bot = PageviewsClient()
    data = view_bot.article_views_new(
        "ar.wikipedia", ["الصفحة الرئيسة"], granularity="monthly", start="20150101", end="20191231"
    )
    # ---
    expected_data = {
        "الصفحة الرئيسة": {
            "2015": 482,
            "2016": 510,
            "2017": 358,
            "2018": 353,
            "2019": 323,
            "all": 2026,
        }
    }
    # ---
    assert isinstance(data, dict)
    assert len(data) > 0
    assert data == expected_data
