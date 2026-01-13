"""
Tests for src.stats_bot_all_years
"""
from src.stats_bot_all_years import dump_stats


def test_dump_stats_with_single_year_data():
    """Test dump_stats with single year integer data"""
    new_data = {"Art1": 10, "Art#1": 5}
    
    stats = dump_stats(["Art1", "Art#1"], new_data, "en")
    
    assert stats["articles"] == 2
    assert stats["hash"] == 1  # Art#1 has hash
    assert stats["views"] == 10  # Only Art1 counted (Art#1 filtered out)
    assert stats["empty"] == 0
    assert stats["not_empty"] == 1


def test_dump_stats_with_multi_year_data():
    """Test dump_stats with multi-year dictionary data"""
    new_data = {
        "Art1": {2020: 50, 2021: 100, 2022: 150},  # Total: 300
        "Art2": {2020: 25, 2021: 75},  # Total: 100
        "Art#1": {2020: 10},  # Has hash, should be filtered
    }
    
    stats = dump_stats(["Art1", "Art2", "Art#1"], new_data, "en")
    
    assert stats["articles"] == 3
    assert stats["hash"] == 1  # Art#1 has hash
    assert stats["views"] == 400  # 300 + 100
    assert stats["empty"] == 0
    assert stats["not_empty"] == 2


def test_dump_stats_with_empty_entries():
    """Test dump_stats correctly identifies empty entries"""
    new_data = {
        "Art1": {2020: 100, 2021: 200},
        "Art2": 0,  # Empty integer
        "Art3": {2020: 0, 2021: 0},  # All years are 0
        "Art4": {2020: 50},
    }
    
    stats = dump_stats(["Art1", "Art2", "Art3", "Art4"], new_data, "en")
    
    assert stats["articles"] == 4
    assert stats["empty"] == 2  # Art2 and Art3
    assert stats["not_empty"] == 2  # Art1 and Art4
    assert stats["views"] == 350  # 300 + 50


def test_dump_stats_with_missing_entries():
    """Test dump_stats when some articles are missing from new_data"""
    new_data = {
        "Art1": {2020: 100},
        "Art2": {2020: 50},
    }
    
    # Art3 is in articles list but not in new_data
    stats = dump_stats(["Art1", "Art2", "Art3"], new_data, "en")
    
    assert stats["articles"] == 3
    assert stats["empty"] == 1  # Art3 is missing, treated as empty
    assert stats["not_empty"] == 1  # Only counting non-empty items in data2 (excluding empty)


def test_dump_stats_with_mixed_data_types():
    """Test dump_stats with mixed integer and dictionary values"""
    new_data = {
        "Art1": {2020: 100, 2021: 150},  # Dict: 250
        "Art2": 75,  # Integer: 75
        "Art3": {2020: 0},  # All zeros
    }
    
    stats = dump_stats(["Art1", "Art2", "Art3"], new_data, "en")
    
    assert stats["articles"] == 3
    assert stats["views"] == 325  # 250 + 75
    assert stats["empty"] == 1  # Art3
    assert stats["not_empty"] == 2


def test_dump_stats_filters_hash_in_articles_list():
    """Test that articles with hash in the original list are filtered"""
    new_data = {
        "Art1": {2020: 100},
        "Art2#section": {2020: 50},  # Has hash in new_data
    }
    
    # Art3#section is in articles list but not in new_data
    stats = dump_stats(["Art1", "Art2#section", "Art3#section"], new_data, "en")
    
    assert stats["hash"] == 2  # Art2#section and Art3#section
    assert stats["views"] == 100  # Only Art1 counted
