import pytest

from src.stats_bot import (
    dump_stats,
    sum_all_views_new,
)


def test_sum_all_views_new():
    # Structure: { ArticleTitle: { year/all: count } }
    new_data = {
        "Art1": {"2020": 10, "all": 20},
        "Art2": {"2020": 5, "2021": 5, "all": 10},
    }

    # Expected:
    # "2020": 10 + 5 = 15
    # "2021": 5
    # "all": 20 + 10 = 30

    result = sum_all_views_new(new_data)

    assert result["2020"] == 15
    assert result["2021"] == 5
    assert result["all"] == 30

    # Test filtering
    # key < 2015 should be removed unless it's "all" or value > 0?
    # Logic: if (k.isnumeric() and int(k) >= 2015) or k == "all" or v > 0

    # Case: Old year, 0 value -> Removed
    data_old_zero = {"Art1": {"2010": 0}}
    res_old_zero = sum_all_views_new(data_old_zero)
    assert "2010" not in res_old_zero

    # Case: Old year, positive value -> Kept (v > 0)
    data_old_pos = {"Art1": {"2010": 5}}
    res_old_pos = sum_all_views_new(data_old_pos)
    assert res_old_pos["2010"] == 5

    # Case: New year, 0 value -> Kept (int(k) >= 2015)
    data_new_zero = {"Art1": {"2020": 0}}
    res_new_zero = sum_all_views_new(data_new_zero)
    assert "2020" in res_new_zero
    assert res_new_zero["2020"] == 0


@pytest.mark.skip(reason="Pending write")
def test_dump_stats():
    # TODO: Implement test
    pass


@pytest.mark.skip(reason="Pending write")
def test_update_all_stats():
    # TODO: Implement test
    pass
