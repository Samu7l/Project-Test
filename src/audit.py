"""Phase 1 audit: read the raw sources once and print the facts recorded in docs/data_audit.md.

Run from the project root:  python -m src.audit
The script only reads data/raw/ and prints; it writes nothing.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
ID_COLS = ["Code Commune", "Commune", "Code QPV", "Nom QPV", "Département", "Région", "Statut géo", "Code", "Fédération"]
GEOC = "1.Champ geoc"
DISABILITY_CODES = ["501", "503"]  # FF Handisport, FF du Sport Adapté (liste-federations.xlsx)
CLUB_ADDRESS_CODES = ["604", "605"]  # UNSS, USEP: licences located at the club, not the home


def read_census(name: str) -> pd.DataFrame:
    """Read a licences or clubs CSV: codes as strings, counts as integers."""
    df = pd.read_csv(RAW / name, sep=";", encoding="utf-8-sig", dtype=str)
    counts = [c for c in df.columns if c not in ID_COLS]
    df[counts] = df[counts].astype("int64")
    return df


def pct(part: float, whole: float) -> str:
    """Format a share as a percentage with two decimals."""
    return f"{100 * part / whole:.2f} %"


def section(title: str) -> None:
    """Print a section header."""
    print(f"\n## {title}")


def audit_licences(lic: pd.DataFrame, communes: pd.DataFrame) -> None:
    """Structure, totals, sex/age completeness, geocoding status, QPV and commune join rate."""
    f_cols = [c for c in lic.columns if c.startswith("F - ")]
    h_cols = [c for c in lic.columns if c.startswith("H - ")]
    total = lic["Total"].sum()
    f, h = lic[f_cols].sum().sum(), lic[h_cols].sum().sum()

    section("S1 lic-data-2023")
    print(f"rows {len(lic):,} | columns {lic.shape[1]} | federations {lic['Code'].nunique()}")
    print(f"total licences {total:,}")
    print(f"F {f:,} ({pct(f, f + h)} of F+H) | H {h:,} | Total - (F+H) = {total - f - h:,} (sex not reported)")
    row_gap = (lic["Total"] != lic[f_cols + h_cols].sum(axis=1)).sum()
    print(f"rows where Total != F+H: {row_gap:,}")
    age_nr = lic["F - NR"].sum() + lic["H - NR"].sum()
    print(f"age not reported (F - NR + H - NR) {age_nr:,} = {pct(age_nr, total)}")
    print("age bands:", ", ".join(c[4:] for c in f_cols))
    print("negative values:", int((lic[f_cols + h_cols + ['Total']] < 0).sum().sum()))

    print("\nStatut géo (licences):")
    for k, v in lic.groupby("Statut géo")["Total"].sum().items():
        print(f"  {k}: {v:,} ({pct(v, total)})")
    geoc = lic[lic["Statut géo"] == GEOC]
    nr = lic[lic["Statut géo"] != GEOC]
    print("non-geocoded licences by federation (top 8):")
    print(nr.groupby(["Code", "Fédération"])["Total"].sum().nlargest(8).to_string())

    print("\nCode QPV kinds (geocoded licences):")
    kind = geoc["Code QPV"].str.slice(0, 2).where(geoc["Code QPV"].str.match(r"Q[PN]"), geoc["Code QPV"])
    for k, v in geoc.groupby(kind)["Total"].sum().items():
        print(f"  {k}: {v:,} ({pct(v, geoc['Total'].sum())})")
    print(f"distinct QPV codes: {geoc.loc[geoc['Code QPV'].str.match(r'Q[PN]'), 'Code QPV'].nunique()}")

    section("Federation checks")
    fed = lic.groupby(["Code", "Fédération"])["Total"].sum().sort_values(ascending=False)
    print("top 5:\n" + fed.head(5).to_string())
    for codes, label in [(DISABILITY_CODES, "disability"), (CLUB_ADDRESS_CODES, "club-address (UNSS/USEP)")]:
        sub = fed[fed.index.get_level_values("Code").isin(codes)]
        print(f"{label}: {sub.to_dict()} -> {pct(sub.sum(), total)} of all licences")
    print(f"federations with >= 1,000 licences: {(fed >= 1000).sum()} / {len(fed)}")

    section("Commune join (geocoded licences) vs geo.api (COG 2026)")
    by_com = geoc.groupby(["Code Commune", "Commune"])["Total"].sum().reset_index()
    by_com["ok"] = by_com["Code Commune"].isin(communes["code"])
    print(f"distinct communes {len(by_com):,} | matched {by_com['ok'].sum():,} ({pct(by_com['ok'].sum(), len(by_com))})")
    print(f"licences matched: {pct(by_com.loc[by_com['ok'], 'Total'].sum(), by_com['Total'].sum())}")
    miss = by_com[~by_com["ok"]].sort_values("Total", ascending=False)
    print(f"unmatched communes: {len(miss)} ({miss['Total'].sum():,} licences); top 10:")
    print(miss.head(10).to_string(index=False))
    print(f"départements in geocoded licences: {geoc['Département'].nunique()} -> {sorted(geoc['Département'].unique())}")


def audit_clubs(clubs: pd.DataFrame) -> None:
    """Structure, totals, geocoding status and QPV share of clubs."""
    section("S2 clubs-data-2023")
    print(f"rows {len(clubs):,} | federations {clubs['Code'].nunique()}")
    tot = clubs[["Clubs_actifs", "EPA_actifs", "Total_actifs", "Clubs", "EPA", "Total"]].sum()
    print(tot.to_string())
    print("Total == Clubs + EPA on every row:", bool((clubs["Total"] == clubs["Clubs"] + clubs["EPA"]).all()))
    print("Total_actifs <= Total on every row:", bool((clubs["Total_actifs"] <= clubs["Total"]).all()))
    for k, v in clubs.groupby("Statut géo")["Total_actifs"].sum().items():
        print(f"  {k}: {v:,} ({pct(v, tot['Total_actifs'])})")
    geoc = clubs[clubs["Statut géo"] == GEOC]
    in_qpv = geoc["Code QPV"].str.match(r"Q[PN]")
    print(f"active structures located in a QPV: {geoc.loc[in_qpv, 'Total_actifs'].sum():,} "
          f"({pct(geoc.loc[in_qpv, 'Total_actifs'].sum(), geoc['Total_actifs'].sum())} of geocoded)")


def audit_population(communes: pd.DataFrame) -> pd.DataFrame:
    """geo.api communes vs the INSEE 2023 reference population file (to identify the millésime)."""
    section("R1 population (geo.api.gouv.fr)")
    print(f"communes {len(communes):,} | with population {communes['population'].notna().sum():,} "
          f"| total {communes['population'].sum():,.0f} | départements {communes['codeDepartement'].nunique()}")
    insee = pd.read_csv(RAW / "DS_POPULATIONS_REFERENCE_2023_data.csv", sep=";", dtype={"GEO": str})
    pmun = insee[(insee["GEO_OBJECT"] == "COM") & (insee["POPREF_MEASURE"] == "PMUN")][["GEO", "OBS_VALUE"]]
    m = communes.merge(pmun, left_on="code", right_on="GEO", how="left")
    same = (m["population"] == m["OBS_VALUE"]).sum()
    print(f"INSEE 2023 file: {len(pmun):,} communes (PMUN) | total {pmun['OBS_VALUE'].sum():,}")
    print(f"geo.api population == INSEE PMUN 2023 for {same:,} / {len(communes):,} communes")
    fr = insee[(insee["GEO_OBJECT"] == "FRANCE")]
    print("INSEE FRANCE rows:\n" + fr.to_string(index=False))
    return communes


def audit_geometry(lic_deps: set[str]) -> None:
    """Département GeoJSON codes vs licence département codes; sample commune contour size."""
    section("R2 départements GeoJSON")
    gj = json.loads((RAW / "departements-version-simplifiee.geojson").read_text())
    codes = {f["properties"]["code"] for f in gj["features"]}
    print(f"features {len(codes)} | properties {list(gj['features'][0]['properties'])}")
    print(f"licence départements missing from GeoJSON: {sorted(lic_deps - codes)}")
    print(f"GeoJSON départements missing from licences: {sorted(codes - lic_deps)}")


def main() -> None:
    """Run every audit section in order."""
    communes = pd.DataFrame(json.loads((RAW / "geoapi_communes.json").read_text()))
    lic = read_census("lic-data-2023.csv")
    clubs = read_census("clubs-data-2023.csv")
    audit_licences(lic, communes)
    audit_clubs(clubs)
    audit_population(communes)
    audit_geometry(set(lic.loc[lic["Statut géo"] == GEOC, "Département"]))


if __name__ == "__main__":
    main()
