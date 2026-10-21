"""R5: municipal population of the 2024 priority neighbourhoods (QPV), INSEE (published 10/07/2025).

Reference date: 1 January 2020 (mainland), 1 January 2021 (Guadeloupe, Martinique, Guyane, La Réunion).
Used only as a benchmark: "share of the population living in a QPV".
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.sources.population import study_departements

URL = "https://www.insee.fr/fr/statistiques/fichier/8210600/pop_QPV24.xlsx"


def read_qpv_population(path: Path) -> pd.DataFrame:
    """One row per QPV of the study scope: code, name, département, municipal population."""
    df = pd.read_excel(path, sheet_name=0, header=7, dtype=str)  # row 8 holds the short variable names
    df = df.rename(columns={"codeQPV": "qpv", "libQPV": "qpv_name", "listeDep": "dep", "popMuniQPV": "population"})
    df = df[["qpv", "qpv_name", "dep", "population"]].astype({"population": "int64"})
    if df["dep"].str.len().gt(3).any():
        raise ValueError("a QPV spans several départements: the département sum needs a split rule")
    return df[study_departements(df["dep"])].reset_index(drop=True)
