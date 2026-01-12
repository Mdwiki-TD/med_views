import json

import pytest

from src.helps import (
    get_views_all_file,
    is_empty_data,
    json_load,
)


def test_is_empty_data():
    assert is_empty_data({}) is True
    assert is_empty_data(None) is True

    # "all": 0 case
    assert is_empty_data({"all": 0, "other": 100}) is True

    # len(data) == 1 case
    assert is_empty_data({"all": 100}) is True
    assert is_empty_data({"some_year": 50}) is True

    # Not empty
    assert is_empty_data({"all": 100, "2023": 50}) is False
    assert is_empty_data({"all": 100, "2023": 50, "2022": 50}) is False


def test_json_load(tmp_path):
    # Test valid dict json
    f = tmp_path / "test.json"
    data = {"key_1": "value", "key_2": 123}
    f.write_text(json.dumps(data), encoding="utf-8")

    loaded = json_load(str(f))
    assert loaded["key 1"] == "value"  # underscore replacement
    assert loaded["key 2"] == 123

    # Test valid list json
    f2 = tmp_path / "test_list.json"
    data_list = ["item_1", "item_2"]
    f2.write_text(json.dumps(data_list), encoding="utf-8")

    loaded_list = json_load(str(f2))
    assert loaded_list == ["item 1", "item 2"]

    # Test file not found
    assert json_load(str(tmp_path / "nonexistent.json")) is None

    # Test invalid json
    f3 = tmp_path / "bad.json"
    f3.write_text("{bad json", encoding="utf-8")
    assert json_load(str(f3)) is None


@pytest.mark.skip(reason="Pending write")
def test_get_views_all_file():
    # TODO: Implement test
    pass
