"""R1: legal population 2023 (INSEE, via geo.api.gouv.fr, COG 2026) and département / region names."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

GEO_API = "https://geo.api.gouv.fr"
COMMUNES_URL = f"{GEO_API}/communes?fields=code,nom,population,codeDepartement,codeRegion&format=json"
ARRONDISSEMENTS_URL = f"{GEO_API}/communes?type=arrondissement-municipal&fields=code,nom,population,codeDepartement&format=json"
DEPARTEMENTS_URL = f"{GEO_API}/departements?fields=code,nom,codeRegion&format=json"
REGIONS_URL = f"{GEO_API}/regions?fields=code,nom&format=json"
INSEE_POP_FILE = "DS_POPULATIONS_REFERENCE_2023_data.csv"  # INSEE reference populations 2023 (cross-check)

OVERSEAS = ["971", "972", "973", "974"]  # DROM in the licence geocoding scope (Mayotte 976 is out of scope)


def study_departements(codes: pd.Series) -> pd.Series:
    """True for the 100 départements of the geocoding scope: mainland (2-character codes) + 971-974."""
    return codes.str.len().eq(2) | codes.isin(OVERSEAS)


def read_communes(path: Path) -> pd.DataFrame:
    """Current communes (COG 2026) of the study scope with their 2023 legal population."""
    com = pd.DataFrame(json.loads(path.read_text()))
    com = com[study_departements(com["codeDepartement"])]
    return com.rename(columns={"code": "com", "nom": "com_name", "codeDepartement": "dep", "codeRegion": "reg"})[
        ["com", "com_name", "dep", "reg", "population"]
    ].astype({"population": "int64"}).reset_index(drop=True)


def read_departements(dep_path: Path, reg_path: Path, communes: pd.DataFrame) -> pd.DataFrame:
    """Départements of the study scope with names, region and population (sum of their communes)."""
    dep = pd.DataFrame(json.loads(dep_path.read_text())).rename(columns={"code": "dep", "nom": "dep_name", "codeRegion": "reg"})
    reg = pd.DataFrame(json.loads(reg_path.read_text())).rename(columns={"code": "reg", "nom": "reg_name"})
    pop = communes.groupby("dep", as_index=False)["population"].sum()
    dep = dep[study_departements(dep["dep"])].merge(reg, on="reg", how="left").merge(pop, on="dep", how="left")
    return dep.assign(is_overseas=dep["dep"].isin(OVERSEAS)).reset_index(drop=True)


def read_insee_population(path: Path, level: str) -> pd.Series:
    """INSEE PMUN 2023 by geographic code for one level ('COM', 'DEP' or 'FRANCE')."""
    df = pd.read_csv(path, sep=";", dtype={"GEO": str})
    df = df[(df["GEO_OBJECT"] == level) & (df["POPREF_MEASURE"] == "PMUN")]
    return df.set_index("GEO")["OBS_VALUE"].astype("int64")
