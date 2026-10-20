"""S1 and S2: geocoded licences and clubs 2023 (INJEP-MEDES census, geocoded by INSEE, data.gouv.fr)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATASET = (
    "https://static.data.gouv.fr/resources/donnees-geocodees-issues-du-recensement-des-licences-et-clubs-aupres-"
    "des-federations-sportives-agreees-par-le-ministere-charge-des-sports"
)
LICENCES_URL = f"{DATASET}/20251229-163107/lic-data-2023.csv"
CLUBS_URL = f"{DATASET}/20251229-163249/clubs-data-2023.csv"

ID_COLS = ["Code Commune", "Commune", "Code QPV", "Nom QPV", "Département", "Région", "Statut géo", "Code", "Fédération"]
GEOCODED = "1.Champ geoc"            # mainland + DROM except Mayotte
NOT_ALLOCATED = "NR - Non réparti"   # value of Code Commune / Code QPV when the federation gave départements only
QPV_PATTERN = r"^Q[NP]"              # QN = 2024 QPV list, QP = 2015 list (only QN appears in 2023)
AGE_BANDS = [
    "1 à 4 ans", "5 à 9 ans", "10 à 14 ans", "15 à 19 ans", "20 à 24 ans", "25 à 29 ans", "30 à 34 ans",
    "35 à 39 ans", "40 à 44 ans", "45 à 49 ans", "50 à 54 ans", "55 à 59 ans", "60 à 64 ans", "65 à 69 ans",
    "70 à 74 ans", "75 à 79 ans", "80 à 99 ans", "NR",
]
SENIOR_BANDS = ["60 à 64 ans", "65 à 69 ans", "70 à 74 ans", "75 à 79 ans", "80 à 99 ans"]
F_COLS = [f"F - {b}" for b in AGE_BANDS]
H_COLS = [f"H - {b}" for b in AGE_BANDS]


def read_census(path: Path) -> pd.DataFrame:
    """Read a licences or clubs CSV (UTF-8 BOM, ';'): identifiers as strings, counts as int64."""
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    counts = [c for c in df.columns if c not in ID_COLS]
    df[counts] = df[counts].astype("int64")
    return df


def add_licence_features(lic: pd.DataFrame) -> pd.DataFrame:
    """Add the derived counts used everywhere: F, H, 60+, known age, QPV resident, QPV allocated."""
    known_age = [c for c in F_COLS + H_COLS if not c.endswith("NR")]
    is_qpv = lic["Code QPV"].str.match(QPV_PATTERN)
    return lic.assign(
        f=lic[F_COLS].sum(axis=1),
        h=lic[H_COLS].sum(axis=1),
        age_60p=lic[[f"{s} - {b}" for s in "FH" for b in SENIOR_BANDS]].sum(axis=1),
        age_known=lic[known_age].sum(axis=1),
        qpv_in=lic["Total"].where(is_qpv, 0),
        qpv_allocated=lic["Total"].where(lic["Code QPV"] != NOT_ALLOCATED, 0),
    )
