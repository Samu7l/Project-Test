"""Commune codes of the licence files (COG 2024) -> current communes (COG 2026).

Two kinds of codes do not exist in the current commune list:
1. Paris / Lyon / Marseille districts (arrondissements municipaux): mapped to their city.
2. Communes merged after 1 January 2024: mapped with the INSEE list of commune events (v_mvt_commune_2026.csv).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

MVT_URL = "https://www.insee.fr/fr/statistiques/fichier/8740222/v_mvt_commune_2026.csv"
FILE_GEOGRAPHY_DATE = "2024-01-01"  # the 2023 census uses the commune geography of 1 January 2024

# (first district, last district) -> city code
PLM_DISTRICTS = {
    (75101, 75120): "75056",  # Paris
    (69381, 69389): "69123",  # Lyon
    (13201, 13216): "13055",  # Marseille
}


def plm_city(code: str) -> str:
    """Return the city code for a Paris/Lyon/Marseille district code, else the code unchanged."""
    if code.isdigit():
        for (first, last), city in PLM_DISTRICTS.items():
            if first <= int(code) <= last:
                return city
    return code


def merged_commune_map(mvt: pd.DataFrame, current: set[str], since: str = FILE_GEOGRAPHY_DATE) -> dict[str, str]:
    """Old commune code -> current commune code, for communes that disappeared after `since`.

    Uses events where a commune (COM) becomes part of another commune (COM). Chains such as
    A -> B (2025) -> C (2026) are followed until the code exists in `current`.
    """
    ev = mvt[(mvt["DATE_EFF"] > since) & (mvt["TYPECOM_AV"] == "COM") & (mvt["TYPECOM_AP"] == "COM")
             & (mvt["COM_AV"] != mvt["COM_AP"]) & ~mvt["COM_AV"].isin(current)]
    targets = ev.groupby("COM_AV")["COM_AP"].unique()
    ambiguous = targets[targets.map(len) > 1]
    if len(ambiguous):
        raise ValueError(f"commune codes with several successors: {ambiguous.to_dict()}")
    step = targets.map(lambda t: t[0]).to_dict()

    mapping = {}
    for old, new in step.items():
        while new not in current and new in step:
            new = step[new]
        mapping[old] = new
    return mapping


def read_mvt(path: Path) -> pd.DataFrame:
    """Read the INSEE commune events file with codes as strings."""
    return pd.read_csv(path, dtype=str)


def to_current_commune(codes: pd.Series, mapping: dict[str, str]) -> pd.Series:
    """Apply the PLM rule then the merged-commune mapping to a Series of commune codes."""
    city = codes.map(plm_city)
    return city.map(lambda c: mapping.get(c, c))
