"""
"""
import pytest

from src.services.mw_views import (
    PageviewsClient,
)


@pytest.mark.network
def test_pageviewsclient():
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


@pytest.mark.network
def test_pageviewsclient_pam():
    view_bot = PageviewsClient()
    data = view_bot.article_views_new(
        "pam.wikipedia", ["Anatomy"], granularity="monthly", start="20150101", end="2025123100"
    )
    # ---
    expected_data = {
        "Anatomy": {
            "2015": 678,
            "2016": 1757,
            "2017": 1922,
            "2018": 1313,
            "2019": 1404,
            "2020": 1585,
            "2021": 1726,
            "2022": 2146,
            "2023": 1905,
            "2024": 2031,
            "2025": 1911,
            "all": 18378,
        }
    }
    # ---
    assert isinstance(data, dict)
    assert len(data) > 0
    assert data == expected_data, data
