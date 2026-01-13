
from src.stats_bot import (
    dump_stats,
)


def test_dump_stats():

    new_data = {"Art1": 10, "Art#1": 5}

    stats = dump_stats(["Art1", "Art#1"], new_data, "en")

    assert stats["articles"] == 2
    assert stats["hash"] == 1
    assert stats["views"] == 10
