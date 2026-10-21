"""Phase 2: download missing raw files and build the processed tables the app loads.

Run from the project root:  python -m src.build
Inputs: data/raw/ (downloaded if missing). Outputs: data/processed/ (parquet + simplified GeoJSON).
"""
from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

from src import geo
from src.sources import clubs as src_clubs
from src.sources import federations as src_fed
from src.sources import geometry as src_geom
from src.sources import licences as src_lic
from src.sources import population as src_pop
from src.sources import census as src_census
from src.sources import drees as src_drees
from src.sources import qpv as src_qpv

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
# INJEP results: 2023 census (first publication, July 2024) and 2024 census (July 2025, revised 2023 history).
INJEP_2023_ZIP_URL = "https://injep.fr/wp-content/uploads/2024/07/Licences-resultats-2023.zip"
INJEP_2024_ZIP_URL = "https://injep.fr/wp-content/uploads/2025/07/Resultats-recensement-2024.zip"

RAW_FILES = {
    "lic-data-2023.csv": src_lic.LICENCES_URL,
    "clubs-data-2023.csv": src_lic.CLUBS_URL,
    "liste-federations.xlsx": src_fed.LIST_URL,
    "injep_2023/Familles-federations-2023.xlsx": src_fed.FAMILIES_URL,
    "injep_2023/Licences-resultats-2023.zip": INJEP_2023_ZIP_URL,
    "injep_2024/Resultats-recensement-2024.zip": INJEP_2024_ZIP_URL,
    "geoapi_communes.json": src_pop.COMMUNES_URL,
    "geoapi_arrondissements.json": src_pop.ARRONDISSEMENTS_URL,
    "geoapi_departements.json": src_pop.DEPARTEMENTS_URL,
    "geoapi_regions.json": src_pop.REGIONS_URL,
    "departements-version-simplifiee.geojson": src_geom.DEPARTEMENTS_URL,
    "departement-976-mayotte.geojson": src_geom.MAYOTTE_URL,
    "v_mvt_commune_2026.csv": geo.MVT_URL,
    "insee_qpv2024/pop_QPV24.xlsx": src_qpv.URL,
    "drees/Panorama_statistique_2024.xlsx": src_drees.URL,
    "insee_rp2023/DS_RP_TD_POPULATION_AGESEX_PRINC_2023.parquet": src_census.URL,
}
# Accented names inside the INJEP zips break `unzip` on macOS; we extract them under ASCII names.
INJEP_MEMBERS = {
    "injep_2023/Licences-resultats-2023.zip": {"Résultats des licences 2023.xlsx": "injep_licences_2023.xlsx",
                                               "Résultats des clubs 2023.xlsx": "injep_clubs_2023.xlsx"},
    "injep_2024/Resultats-recensement-2024.zip": {"Historique licences 2002-2024.xlsx": "injep_historique_2002_2024.xlsx"},
}


def download(url: str, path: Path) -> None:
    """Download `url` to `path` (browser user-agent: injep.fr refuses the default one)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=300)
    r.raise_for_status()
    path.write_bytes(r.content)


def ensure_raw() -> None:
    """Download every raw file that is not already in data/raw/, then extract the INJEP tables."""
    for name, url in RAW_FILES.items():
        if not (RAW / name).exists():
            print(f"download {name}")
            download(url, RAW / name)
    for archive, members in INJEP_MEMBERS.items():
        folder = (RAW / archive).parent
        with zipfile.ZipFile(RAW / archive) as z:
            for member, target in members.items():
                if not (folder / target).exists():
                    (folder / target).write_bytes(z.read(member))


def ensure_commune_contours(deps: list[str]) -> None:
    """Download raw commune outlines for each département once (geo.api, ~100 calls)."""
    for dep in deps:
        path = RAW / "communes_contours" / f"{dep}.geojson"
        if not path.exists():
            download(src_geom.COMMUNES_URL.format(dep=dep), path)
            time.sleep(0.1)  # be gentle with the public API


def build_licences(lic: pd.DataFrame, code_map: dict[str, str]) -> dict[str, pd.DataFrame]:
    """Département × federation, commune × federation and national pyramid tables."""
    lic = src_lic.add_licence_features(lic)
    measures = ["Total", "f", "h", "age_60p", "age_known", "qpv_in", "qpv_allocated"]
    geoc = lic[lic["Statut géo"] == src_lic.GEOCODED]

    dep_fed = (geoc.groupby(["Département", "Code"], as_index=False)[measures].sum()
               .rename(columns={"Département": "dep", "Code": "code", "Total": "licences"}))

    with_commune = geoc[geoc["Code Commune"] != src_lic.NOT_ALLOCATED]
    com_fed = (with_commune.assign(com=geo.to_current_commune(with_commune["Code Commune"], code_map))
               .groupby(["com", "Code"], as_index=False)[["Total", "f", "h"]].sum()
               .rename(columns={"Code": "code", "Total": "licences"}))

    pyramid = (lic.groupby("Code")[src_lic.F_COLS + src_lic.H_COLS].sum()  # all statuses: national view
               .rename_axis("code").reset_index()
               .melt(id_vars="code", var_name="sex_age", value_name="licences"))
    pyramid[["sex", "age_band"]] = pyramid["sex_age"].str.split(" - ", n=1, expand=True)
    pyramid["age_order"] = pyramid["age_band"].map({b: i for i, b in enumerate(src_lic.AGE_BANDS)})
    pyramid = pyramid.drop(columns="sex_age").sort_values(["code", "sex", "age_order"]).reset_index(drop=True)

    status = (lic.pivot_table(index="Code", columns="Statut géo", values="Total", aggfunc="sum", fill_value=0)
              .rename(columns={"1.Champ geoc": "lic_geocoded", "2.Hors Champ geoc": "lic_out_of_scope",
                               "3.NR": "lic_not_allocated"})
              .rename_axis(index="code", columns=None).reset_index())
    sex = lic.groupby("Code", as_index=False)[["Total", "f", "h"]].sum().rename(
        columns={"Code": "code", "Total": "lic_total", "f": "lic_f", "h": "lic_h"})
    return {"lic_dep_fed": dep_fed, "lic_com_fed": com_fed, "pyramid": pyramid, "fed_licences": sex.merge(status, on="code")}


def build_clubs(clubs: pd.DataFrame, code_map: dict[str, str]) -> dict[str, pd.DataFrame]:
    """Département × federation and commune × federation tables of active clubs and EPA."""
    clubs = src_clubs.add_club_features(clubs)
    measures = ["Clubs_actifs", "EPA_actifs", "Total_actifs", "actifs_qpv_in", "actifs_qpv_allocated"]
    geoc = clubs[clubs["Statut géo"] == src_lic.GEOCODED]
    rename = {"Département": "dep", "Code": "code", "Clubs_actifs": "clubs_actifs", "EPA_actifs": "epa_actifs",
              "Total_actifs": "actifs"}
    dep_fed = geoc.groupby(["Département", "Code"], as_index=False)[measures].sum().rename(columns=rename)
    with_commune = geoc[geoc["Code Commune"] != src_lic.NOT_ALLOCATED]
    com_fed = (with_commune.assign(com=geo.to_current_commune(with_commune["Code Commune"], code_map))
               .groupby(["com", "Code"], as_index=False)["Total_actifs"].sum().rename(columns=rename))
    totals = clubs.groupby("Code", as_index=False)[["Total_actifs", "Total"]].sum().rename(
        columns={"Code": "code", "Total_actifs": "clubs_actifs_total", "Total": "clubs_total"})
    return {"clubs_dep_fed": dep_fed, "clubs_com_fed": com_fed, "fed_clubs": totals}


def build_overseas_outlines(overseas: list[str]) -> dict:
    """Overseas département outlines: 971-974 merged from their commune outlines, Mayotte (976) simplified."""
    features = []
    for dep in overseas:
        communes = src_geom.read_geojson(RAW / "communes_contours" / f"{dep}.geojson")["features"]
        features.append({"type": "Feature", "properties": {"code": dep},
                         "geometry": src_geom.dissolve(communes)})
    mayotte = src_geom.read_geojson(RAW / "departement-976-mayotte.geojson")
    features.append({"type": "Feature", "properties": {"code": "976"},
                     "geometry": src_geom.simplify_geometry(mayotte["geometry"])})
    return {"type": "FeatureCollection", "features": features}


def build_geometries(deps: pd.DataFrame) -> dict[str, int]:
    """Mainland map, overseas outlines and one simplified commune file per département. Returns feature counts."""
    dep_geo = src_geom.read_geojson(RAW / "departements-version-simplifiee.geojson")
    src_geom.write_geojson(dep_geo, PROCESSED / "geo" / "departements_metro.geojson")
    ensure_commune_contours(deps["dep"].tolist())
    overseas = build_overseas_outlines(deps.loc[deps["is_overseas"], "dep"].tolist())
    src_geom.write_geojson(overseas, PROCESSED / "geo" / "departements_overseas.geojson")
    n = 0
    for dep in deps["dep"]:
        simple = src_geom.simplify_communes(src_geom.read_geojson(RAW / "communes_contours" / f"{dep}.geojson"))
        src_geom.write_geojson(simple, PROCESSED / "geo" / "communes" / f"{dep}.geojson")
        n += len(simple["features"])
    return {"departement_features": len(dep_geo["features"]), "overseas_features": len(overseas["features"]),
            "commune_features": n}


def save(tables: dict[str, pd.DataFrame]) -> None:
    """Write each table to data/processed/<name>.parquet and print its shape and size."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        path = PROCESSED / f"{name}.parquet"
        df.to_parquet(path, index=False)
        print(f"  {name:<16} {df.shape[0]:>8,} rows × {df.shape[1]:>2} cols  {path.stat().st_size / 1024:>7,.0f} KB")


def main() -> None:
    """Run the whole build."""
    ensure_raw()
    communes = src_pop.read_communes(RAW / "geoapi_communes.json")
    deps = src_pop.read_departements(RAW / "geoapi_departements.json", RAW / "geoapi_regions.json", communes)
    code_map = geo.merged_commune_map(geo.read_mvt(RAW / "v_mvt_commune_2026.csv"), set(communes["com"]))

    lic_tables = build_licences(src_lic.read_census(RAW / "lic-data-2023.csv"), code_map)
    club_tables = build_clubs(src_lic.read_census(RAW / "clubs-data-2023.csv"), code_map)

    fed = src_fed.read_federations(RAW / "liste-federations.xlsx", RAW / "injep_2023" / "Familles-federations-2023.xlsx")
    fed = (fed.merge(lic_tables.pop("fed_licences"), on="code", how="left")
              .merge(club_tables.pop("fed_clubs"), on="code", how="left"))
    count_cols = fed.select_dtypes("number").columns
    fed[count_cols] = fed[count_cols].fillna(0).astype("int64")

    qpv = src_qpv.read_qpv_population(RAW / "insee_qpv2024" / "pop_QPV24.xlsx")
    equipment = src_drees.read_equipment(RAW / "drees" / "Panorama_statistique_2024.xlsx", deps)
    tables = {"federations": fed, "population_dep": deps, "population_com": communes, "population_qpv": qpv,
              "drees_disabled_adults": equipment,
              "population_sex_age": src_census.population_by_band(
                  src_census.read_departements(RAW / "insee_rp2023" / "DS_RP_TD_POPULATION_AGESEX_PRINC_2023.parquet"),
                  deps["dep"].tolist()),
              **lic_tables, **club_tables}
    print("tables:")
    save(tables)

    report = {
        "built_at": time.strftime("%Y-%m-%d %H:%M"),
        "merged_commune_codes_mapped": len(code_map),
        **build_geometries(deps),
    }
    (PROCESSED / "build_report.json").write_text(json.dumps(report, indent=2))
    print(report)


if __name__ == "__main__":
    main()
