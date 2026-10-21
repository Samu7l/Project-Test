"""Phase 3: validation of the processed tables against the published INJEP figures and internal consistency rules.

Run from the project root:  python -m src.validate
Each check returns a row (check, observed, expected, passed, note). The same table is shown in the app's Data page.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from src.sources import population as src_pop

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
INJEP = RAW / "injep_2023"           # first publication of the 2023 census (July 2024)
INJEP_REVISED = RAW / "injep_2024"   # 2024 census publication (July 2025), with revised 2023 history


@dataclass
class Check:
    """One validation result."""
    group: str
    check: str
    observed: str
    expected: str
    passed: bool
    note: str = ""


def load(name: str) -> pd.DataFrame:
    """Load one processed parquet table."""
    return pd.read_parquet(PROCESSED / f"{name}.parquet")


def read_injep_federation_table(path: Path, sheet: str) -> pd.DataFrame:
    """INJEP federation table: keep rows with a 3-digit federation code; codes as strings."""
    df = pd.read_excel(path, sheet_name=sheet, header=3)
    df = df[pd.to_numeric(df["Code"], errors="coerce").notna()].copy()
    df["code"] = df["Code"].astype(int).astype(str)
    return df.set_index("code")


def fmt(x: float) -> str:
    """Thousands separator for integers, 2 decimals otherwise."""
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:,.2f}"


def read_injep_revised_2023() -> pd.DataFrame:
    """Revised 2023 figures by federation (INJEP 2024 census publication, July 2025): total, F, H."""
    df = pd.read_excel(INJEP_REVISED / "injep_historique_2002_2024.xlsx", sheet_name="4.Lics_sexe_02_24", header=3)
    df = df[(df["Année"] == 2023) & pd.to_numeric(df["Code 2024"], errors="coerce").notna()].copy()
    df["code"] = df["Code 2024"].astype(int).astype(str)
    cols = {"Licences annuelles totales": "total", "Licences annuelles F": "f", "Licences annuelles H": "h"}
    return df.set_index("code")[list(cols)].rename(columns=cols).apply(pd.to_numeric).fillna(0).astype("int64")


def compare_by_federation(ours: pd.Series, published: pd.Series) -> pd.DataFrame:
    """Align two per-federation series (missing = 0) and keep the federations that differ."""
    both = pd.concat({"ours": ours, "published": published}, axis=1).fillna(0).astype("int64")
    return both[both["ours"] != both["published"]]


def checks_published(fed: pd.DataFrame, dep_fed: pd.DataFrame) -> list[Check]:
    """Our totals vs INJEP published results.

    Reference = revised 2023 figures (2024 publication, July 2025). The first 2023 publication (July 2024) is also
    compared: its gaps must come only from federations that INJEP revised afterwards.
    """
    out = []
    ours = fed.set_index("code")
    revised = read_injep_revised_2023()
    for col, label in [("total", "licences"), ("f", "women's licences"), ("h", "men's licences")]:
        mine = ours[{"total": "lic_total", "f": "lic_f", "h": "lic_h"}[col]]
        diff = compare_by_federation(mine, revised[col])
        out.append(Check("Published", f"National {label} = INJEP revised 2023", fmt(mine.sum()),
                         fmt(revised[col].sum()), mine.sum() == revised[col].sum(), "INJEP July 2025, history table"))
        out.append(Check("Published", f"Federations whose {label} equal INJEP revised",
                         f"{len(ours) - len(diff)} / {len(ours)}", f"{len(ours)} / {len(ours)}", diff.empty,
                         "; ".join(f"{c}: {r.ours:,} vs {r.published:,}" for c, r in diff.iterrows())))
    out.append(Check("Published", "Federations with licences", fmt((ours["lic_total"] > 0).sum()),
                     fmt((revised["total"] > 0).sum()), (ours["lic_total"] > 0).sum() == (revised["total"] > 0).sum(),
                     "120 approved federations, 3 of them without licences"))

    first = read_injep_federation_table(INJEP / "injep_licences_2023.xlsx", "1.LicATP")["Licences annuelles (2023)"]
    first = pd.to_numeric(first, errors="coerce").fillna(0)
    revised_codes = set(compare_by_federation(first, revised["total"]).index)
    gap = compare_by_federation(ours["lic_total"], first)
    out.append(Check("Published", "Gap vs first publication (July 2024) explained by INJEP revisions",
                     f"{gap['ours'].sum() - gap['published'].sum():+,} licences in {', '.join(gap.index)}",
                     f"only federations revised by INJEP ({', '.join(sorted(revised_codes))})",
                     set(gap.index) <= revised_codes, "102 Aviron and 128 Voile were revised upwards in 2025"))

    # Département totals. INJEP corrects non-response (it re-allocates non-geocoded licences), so we expect
    # small gaps; the check passes if every département is within 2 %.
    dep_tab = pd.read_excel(INJEP / "injep_licences_2023.xlsx", sheet_name="5b.Dep", header=3)
    dep_cols = [c for c in dep_tab.columns if isinstance(c, str) and c[:3].strip().isalnum() and " - " in c]
    dep_tab = dep_tab[pd.to_numeric(dep_tab["Code"], errors="coerce").notna()]
    injep_dep = dep_tab[dep_cols].apply(pd.to_numeric, errors="coerce").sum()
    injep_dep.index = [c.split(" - ")[0] for c in injep_dep.index]
    our_dep = dep_fed.groupby("dep")["licences"].sum()
    gap = ((our_dep - injep_dep.reindex(our_dep.index)) / injep_dep.reindex(our_dep.index)).dropna()
    worst = gap.abs().idxmax()
    out.append(Check("Published", "Département totals vs INJEP (max |gap|)", f"{gap.abs().max():.2%} ({worst})",
                     "≤ 2 %", gap.abs().max() <= 0.02,
                     f"median |gap| {gap.abs().median():.2%}; ours = geocoded only, INJEP re-allocates non-response"))

    # Clubs: INJEP publishes no revised 2023 clubs table, so we compare with the first publication.
    clubs = read_injep_federation_table(INJEP / "injep_clubs_2023.xlsx", "1.ClubEPA")["Total actifs (2023)"]
    clubs = pd.to_numeric(clubs, errors="coerce").fillna(0)
    club_gap = compare_by_federation(ours["clubs_actifs_total"], clubs)
    out.append(Check("Published", "Active clubs + EPA vs first publication", fmt(ours["clubs_actifs_total"].sum()),
                     fmt(clubs.sum()), set(club_gap.index) <= revised_codes,
                     "gap only in revised federations: " + "; ".join(f"{c}: {r.ours:,} vs {r.published:,}"
                                                                      for c, r in club_gap.iterrows())))
    return out


def checks_internal(fed: pd.DataFrame, dep_fed: pd.DataFrame, com_fed: pd.DataFrame, pyramid: pd.DataFrame,
                    clubs_dep: pd.DataFrame, clubs_com: pd.DataFrame) -> list[Check]:
    """Sums that must match between tables."""
    geocoded = fed["lic_geocoded"].sum()
    dept_only = fed.loc[fed["is_dept_only"], "lic_geocoded"].sum()
    out = [
        Check("Sums", "Σ départements = national geocoded licences", fmt(dep_fed["licences"].sum()), fmt(geocoded),
              dep_fed["licences"].sum() == geocoded),
        Check("Sums", "Σ communes = geocoded − département-only federations", fmt(com_fed["licences"].sum()),
              fmt(geocoded - dept_only), com_fed["licences"].sum() == geocoded - dept_only,
              f"{dept_only:,} licences of Défense / Maccabi / Police have no commune"),
        Check("Sums", "Σ pyramid (sex × age) = national total", fmt(pyramid["licences"].sum()),
              fmt(fed["lic_total"].sum()), pyramid["licences"].sum() == fed["lic_total"].sum()),
        Check("Sums", "Licences = women + men in every département × federation",
              fmt((dep_fed["licences"] != dep_fed["f"] + dep_fed["h"]).sum()) + " rows differ", "0 rows differ",
              (dep_fed["licences"] == dep_fed["f"] + dep_fed["h"]).all(), "sex is never missing"),
        Check("Sums", "QPV residents ≤ QPV-allocated ≤ licences (every row)",
              "ok" if ((dep_fed["qpv_in"] <= dep_fed["qpv_allocated"]) & (dep_fed["qpv_allocated"] <= dep_fed["licences"])).all() else "violated",
              "ok", ((dep_fed["qpv_in"] <= dep_fed["qpv_allocated"]) & (dep_fed["qpv_allocated"] <= dep_fed["licences"])).all()),
        Check("Sums", "QPV-allocated = licences − département-only federations", fmt(dep_fed["qpv_allocated"].sum()),
              fmt(geocoded - dept_only), dep_fed["qpv_allocated"].sum() == geocoded - dept_only),
        Check("Sums", "Σ clubs by commune ≤ Σ clubs by département", fmt(clubs_com["actifs"].sum()),
              f"≤ {clubs_dep['actifs'].sum():,}", clubs_com["actifs"].sum() <= clubs_dep["actifs"].sum(),
              f"{clubs_dep['actifs'].sum() - clubs_com['actifs'].sum():,} active structures given by département only"),
    ]
    return out


def checks_joins(dep_fed: pd.DataFrame, com_fed: pd.DataFrame, clubs_com: pd.DataFrame, pop_com: pd.DataFrame,
                 pop_dep: pd.DataFrame) -> list[Check]:
    """Join rates between the census tables and the population / geometry files."""
    out = []
    for label, df, col in [("licences", com_fed, "licences"), ("clubs", clubs_com, "actifs")]:
        ok = df["com"].isin(pop_com["com"])
        out.append(Check("Joins", f"Commune join rate ({label}, weighted)", f"{df.loc[ok, col].sum() / df[col].sum():.4%}",
                         "100 %", ok.all(), f"{df.loc[~ok, 'com'].nunique()} codes unmatched; after PLM + merged-commune mapping"))
    com_dep = com_fed.merge(pop_com[["com", "dep"]], on="com")
    out.append(Check("Joins", "Département join rate (licences → population)",
                     f"{dep_fed['dep'].isin(pop_dep['dep']).mean():.2%}", "100 %", dep_fed["dep"].isin(pop_dep["dep"]).all()))
    # Commune → département consistency: the commune's current département gives the same totals as the file's column.
    by_com_dep = com_dep.groupby("dep")["licences"].sum()
    by_file_dep = (dep_fed.merge(load("federations")[["code", "is_dept_only"]], on="code")
                   .query("~is_dept_only").groupby("dep")["licences"].sum())
    out.append(Check("Joins", "Départements rebuilt from communes = file départements",
                     f"{(by_com_dep.reindex(by_file_dep.index) == by_file_dep).sum()} / {len(by_file_dep)}",
                     f"{len(by_file_dep)} / {len(by_file_dep)}", by_com_dep.reindex(by_file_dep.index).eq(by_file_dep).all()))

    geo = json.loads((PROCESSED / "geo" / "departements_metro.geojson").read_text())
    geo_codes = {f["properties"]["code"] for f in geo["features"]}
    metro = set(pop_dep.loc[~pop_dep["is_overseas"], "dep"])
    out.append(Check("Joins", "Mainland départements with a map shape", f"{len(metro & geo_codes)} / {len(metro)}",
                     f"{len(metro)} / {len(metro)}", metro <= geo_codes, "overseas 971–974 shown in a table under the map"))
    om = json.loads((PROCESSED / "geo" / "departements_overseas.geojson").read_text())
    om_codes = {f["properties"]["code"] for f in om["features"]}
    overseas = set(pop_dep.loc[pop_dep["is_overseas"], "dep"]) | {"976"}
    out.append(Check("Joins", "Overseas départements with a map shape (incl. Mayotte, no data)",
                     f"{len(overseas & om_codes)} / {len(overseas)}", f"{len(overseas)} / {len(overseas)}",
                     overseas <= om_codes, "971–974 merged from commune outlines; 976 from france-geojson"))
    missing = 0
    for dep, com in pop_com.groupby("dep")["com"]:
        shapes = json.loads((PROCESSED / "geo" / "communes" / f"{dep}.geojson").read_text())
        missing += len(set(com) - {f["properties"]["code"] for f in shapes["features"]})
    out.append(Check("Joins", "Communes with a shape (drill-down)", f"{len(pop_com) - missing:,} / {len(pop_com):,}",
                     f"{len(pop_com):,} / {len(pop_com):,}", missing == 0))
    return out


def checks_population(pop_com: pd.DataFrame, pop_dep: pd.DataFrame) -> list[Check]:
    """geo.api population vs the INSEE reference population 2023 file."""
    path = RAW / src_pop.INSEE_POP_FILE
    insee_com = src_pop.read_insee_population(path, "COM")
    insee_dep = src_pop.read_insee_population(path, "DEP")
    insee_fr = src_pop.read_insee_population(path, "FRANCE")["F"]
    same_com = (pop_com.set_index("com")["population"] == insee_com.reindex(pop_com["com"]).values).sum()
    same_dep = (pop_dep.set_index("dep")["population"] == insee_dep.reindex(pop_dep["dep"]).values).sum()
    return [
        Check("Population", "Communes: geo.api = INSEE PMUN 2023", f"{same_com:,} / {len(pop_com):,}",
              f"{len(pop_com):,} / {len(pop_com):,}", same_com == len(pop_com), "population municipale, millésime 2023"),
        Check("Population", "Départements: Σ communes = INSEE PMUN 2023", f"{same_dep} / {len(pop_dep)}",
              f"{len(pop_dep)} / {len(pop_dep)}", same_dep == len(pop_dep)),
        Check("Population", "Study area = INSEE France excl. Mayotte", fmt(pop_dep["population"].sum()), fmt(insee_fr),
              pop_dep["population"].sum() == insee_fr),
    ]


def checks_qpv(pop_dep: pd.DataFrame, pop_qpv: pd.DataFrame) -> list[Check]:
    """QPV codes of the licence and club files vs the INSEE QPV 2024 population file."""
    lic = pd.read_csv(RAW / "lic-data-2023.csv", sep=";", encoding="utf-8-sig", dtype=str,
                      usecols=["Code QPV", "Statut géo"])
    codes = set(lic.loc[lic["Code QPV"].str.match(r"^Q[NP]"), "Code QPV"])
    clubs = pd.read_csv(RAW / "clubs-data-2023.csv", sep=";", encoding="utf-8-sig", dtype=str, usecols=["Code QPV"])
    club_codes = set(clubs.loc[clubs["Code QPV"].str.match(r"^Q[NP]"), "Code QPV"])
    known = set(pop_qpv["qpv"])
    share = pop_qpv["population"].sum() / pop_dep["population"].sum()
    return [
        Check("QPV", "Licence QPV codes found in INSEE QPV 2024 file", f"{len(codes & known)} / {len(codes)}",
              f"{len(codes)} / {len(codes)}", codes <= known, "all codes are 2024 QPV (QN…)"),
        Check("QPV", "Club QPV codes found in INSEE QPV 2024 file", f"{len(club_codes & known)} / {len(club_codes)}",
              f"{len(club_codes)} / {len(club_codes)}", club_codes <= known),
        Check("QPV", "QPV in the study area with at least one licence", f"{len(codes & known)} / {len(known)}",
              "information", True, f"QPV population {pop_qpv['population'].sum():,} = {share:.2%} of the population "
                                   "(QPV pop. 2020/2021, total pop. 2023)"),
    ]


def run_all() -> pd.DataFrame:
    """Run every check and return them as a DataFrame."""
    fed, dep_fed, com_fed, pyramid = load("federations"), load("lic_dep_fed"), load("lic_com_fed"), load("pyramid")
    clubs_dep, clubs_com = load("clubs_dep_fed"), load("clubs_com_fed")
    pop_com, pop_dep = load("population_com"), load("population_dep")
    checks = (checks_published(fed, dep_fed)
              + checks_internal(fed, dep_fed, com_fed, pyramid, clubs_dep, clubs_com)
              + checks_joins(dep_fed, com_fed, clubs_com, pop_com, pop_dep)
              + checks_population(pop_com, pop_dep)
              + checks_qpv(pop_dep, load("population_qpv")))
    return pd.DataFrame([asdict(c) for c in checks])


def main() -> None:
    """Print the validation table and save it for the app."""
    res = run_all()
    res.to_parquet(PROCESSED / "validation.parquet", index=False)
    with pd.option_context("display.width", 250, "display.max_colwidth", 110):
        print(res.to_string(index=False))
    print(f"\n{res['passed'].sum()} / {len(res)} checks passed")


if __name__ == "__main__":
    main()
