"""Unit tests for commune code mapping (src/geo.py)."""
import pandas as pd
import pytest

from src import geo


def mvt(rows: list[tuple[str, str, str]]) -> pd.DataFrame:
    """Build a tiny INSEE events table from (date, old code, new code) merges between communes."""
    return pd.DataFrame([{"DATE_EFF": d, "TYPECOM_AV": "COM", "COM_AV": a, "TYPECOM_AP": "COM", "COM_AP": b}
                         for d, a, b in rows])


def test_plm_districts_map_to_their_city():
    assert geo.plm_city("75115") == "75056"
    assert geo.plm_city("69383") == "69123"
    assert geo.plm_city("13208") == "13055"
    assert geo.plm_city("75056") == "75056"  # the city itself is unchanged
    assert geo.plm_city("2A004") == "2A004"  # Corsican codes are not numeric


def test_merge_after_file_date_is_mapped():
    m = geo.merged_commune_map(mvt([("2025-01-01", "93059", "93066")]), current={"93066"})
    assert m == {"93059": "93066"}


def test_merge_before_file_date_is_ignored():
    m = geo.merged_commune_map(mvt([("2023-01-01", "01001", "01002")]), current={"01002"})
    assert m == {}


def test_chains_are_followed_to_a_current_commune():
    m = geo.merged_commune_map(mvt([("2025-01-01", "A", "B"), ("2026-01-01", "B", "C")]), current={"C"})
    assert m == {"A": "C", "B": "C"}


def test_ambiguous_successor_raises():
    with pytest.raises(ValueError):
        geo.merged_commune_map(mvt([("2025-01-01", "A", "B"), ("2025-01-01", "A", "C")]), current={"B", "C"})


def test_to_current_commune_applies_both_rules():
    codes = pd.Series(["75101", "93059", "01001"])
    assert geo.to_current_commune(codes, {"93059": "93066"}).tolist() == ["75056", "93066", "01001"]
