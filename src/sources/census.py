"""R7: INSEE census 2023, population by sex and single year of age (table POP1), by département.

Ages are regrouped into the licence file's bands: 1–4 (age 0 left out), 5-year bands, 80–99 (100+ left out).
Sex codes follow the licence file: F (women), H (men; census code M).
Values are census estimates with decimals: they are kept as floats and rounded only for display.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.sources.licences import AGE_BANDS

URL = "https://www.insee.fr/fr/statistiques/fichier/9006235/DS_RP_TD_POPULATION_AGESEX_PRINC_2023.parquet"
SEX = {"F": "F", "M": "H"}  # census -> licence file


def band_of_age(age: int) -> str | None:
    """Licence age band of a single year of age ('1 à 4 ans', ..., '80 à 99 ans'); None for 0 and 100+."""
    if age < 1 or age > 99:
        return None
    if age <= 4:
        return "1 à 4 ans"
    if age >= 80:
        return "80 à 99 ans"
    low = age // 5 * 5
    return f"{low} à {low + 4} ans"


def read_departements(path: Path) -> pd.DataFrame:
    """Raw census rows for the département level: dep, sex (F/M/_T), age (Y0…Y99, Y_GE100, _T), population."""
    df = pd.read_parquet(path, columns=["GEO", "GEO_OBJECT", "AGE", "SEX", "OBS_VALUE"],
                         filters=[("GEO_OBJECT", "==", "DEP")])
    return (df.astype({"GEO": str, "AGE": str, "SEX": str})
              .rename(columns={"GEO": "dep", "AGE": "age", "SEX": "sex", "OBS_VALUE": "population"})
              [["dep", "sex", "age", "population"]])


def population_by_band(raw: pd.DataFrame, deps: list[str]) -> pd.DataFrame:
    """Long table dep × sex (F/H) × age_band (licence bands) × population (float), for the study départements."""
    single = raw[raw["age"].str.fullmatch(r"Y\d+") & raw["sex"].isin(list(SEX)) & raw["dep"].isin(deps)].copy()
    single["age_band"] = single["age"].str[1:].astype(int).map(band_of_age)
    single = single.dropna(subset=["age_band"])
    single["sex"] = single["sex"].map(SEX)
    out = single.groupby(["dep", "sex", "age_band"], as_index=False)["population"].sum()
    out["age_order"] = out["age_band"].map({b: i for i, b in enumerate(AGE_BANDS)})
    return out.sort_values(["dep", "sex", "age_order"]).reset_index(drop=True)
