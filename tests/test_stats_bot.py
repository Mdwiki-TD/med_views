from unittest.mock import MagicMock

from src.stats_bot import (
    dump_stats,
)


def test_dump_stats(monkeypatch):

    mock_dump = MagicMock()
    monkeypatch.setattr("src.stats_bot.dump_one", mock_dump)

    new_data = {"Art1": 10, "Art#1": 5}

    stats = dump_stats(["Art1", "Art#1"], new_data, "en")

    assert stats["articles"] == 2
    assert stats["hash"] == 1
    assert stats["views"] == 10
    mock_dump.assert_called_once()
