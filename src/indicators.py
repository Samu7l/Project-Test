"""Indicators: scopes, rates per 10,000 inhabitants, rankings, national summary. Pure pandas (no Streamlit)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

PER = 10_000            # rates are "licences per 10,000 inhabitants"
MIN_COMMUNE_POP = 2_000  # communes below this population get no rate (small numbers give extreme values)
ALL = "ALL"             # value of the federation filter meaning "every federation in scope"


def territory_codes(fed: pd.DataFrame) -> list[str]:
    """Federations used on the Territories page.

    Excluded: school sport located at the school (UNSS, USEP) and federations reported by département only
    (Défense, Maccabi, Police), so that the département map and the commune drill-down count the same licences.
    """
    keep = fed["in_geo_views"] & ~fed["is_dept_only"] & (fed["lic_total"] > 0)
    return fed.loc[keep, "code"].tolist()


def selected_codes(fed: pd.DataFrame, federation: str) -> list[str]:
    """Federation codes for the sidebar filter: every territory federation, or the single one selected."""
    return territory_codes(fed) if federation == ALL else [federation]


def rate(licences: pd.Series, population: pd.Series) -> pd.Series:
    """Licences per 10,000 inhabitants."""
    return licences / population * PER


def departement_rates(lic_dep_fed: pd.DataFrame, pop_dep: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    """One row per département (all 100): licences, population, rate and rank (1 = highest rate)."""
    lic = lic_dep_fed[lic_dep_fed["code"].isin(codes)].groupby("dep")["licences"].sum()
    df = pop_dep.assign(licences=pop_dep["dep"].map(lic).fillna(0).astype("int64"))
    df["rate"] = rate(df["licences"], df["population"])
    df["rank"] = df["rate"].rank(ascending=False, method="min").astype(int)
    return df.sort_values("rank").reset_index(drop=True)


def national_rate(dep_rates: pd.DataFrame) -> float:
    """Rate for the whole study area (100 départements)."""
    return float(rate(dep_rates["licences"].sum(), dep_rates["population"].sum()))


def commune_rates(lic_com_fed: pd.DataFrame, pop_com: pd.DataFrame, codes: list[str], dep: str,
                  min_pop: int = MIN_COMMUNE_POP) -> pd.DataFrame:
    """Communes of one département: licences, population, and a rate only when population ≥ `min_pop`."""
    communes = pop_com[pop_com["dep"] == dep]
    lic = lic_com_fed[lic_com_fed["com"].isin(communes["com"]) & lic_com_fed["code"].isin(codes)]
    lic = lic.groupby("com")["licences"].sum()
    df = communes.assign(licences=communes["com"].map(lic).fillna(0).astype("int64"))
    df["above_threshold"] = df["population"] >= min_pop
    df["rate"] = rate(df["licences"], df["population"]).where(df["above_threshold"])
    return df.sort_values("rate", ascending=False).reset_index(drop=True)


@dataclass
class NationalSummary:
    """Headline numbers for the Hook page."""
    licences: int            # all licences, all federations, all geocoding statuses
    school_licences: int     # UNSS + USEP (included in `licences`)
    women_share: float       # F / (F + H)
    active_structures: int   # active clubs + EPA (≥ 1 annual licence)
    federations: int


def national_summary(fed: pd.DataFrame) -> NationalSummary:
    """National totals from the federation table."""
    return NationalSummary(
        licences=int(fed["lic_total"].sum()),
        school_licences=int(fed.loc[fed["is_club_address"], "lic_total"].sum()),
        women_share=float(fed["lic_f"].sum() / (fed["lic_f"].sum() + fed["lic_h"].sum())),
        active_structures=int(fed["clubs_actifs_total"].sum()),
        federations=int((fed["lic_total"] > 0).sum()),
    )


# --- QPV ---------------------------------------------------------------------------------------------------------
def qpv_shares(lic_dep_fed: pd.DataFrame, clubs_dep_fed: pd.DataFrame, pop_dep: pd.DataFrame,
               pop_qpv: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    """By département: share of licences held by QPV residents, of active clubs/EPA located in a QPV, and of the
    population living in a QPV. Shares are fractions (0-1).

    Denominators exclude records with no QPV information (`NR`, the département-only federations).
    """
    lic = lic_dep_fed[lic_dep_fed["code"].isin(codes)].groupby("dep")[["qpv_in", "qpv_allocated"]].sum()
    clubs = (clubs_dep_fed[clubs_dep_fed["code"].isin(codes)]
             .groupby("dep")[["actifs_qpv_in", "actifs_qpv_allocated"]].sum())
    qpv_pop = pop_qpv.groupby("dep")["population"].sum().rename("qpv_population")
    df = (pop_dep.set_index("dep").join([lic, clubs, qpv_pop]).fillna(0).reset_index())
    df["lic_share"] = df["qpv_in"] / df["qpv_allocated"]
    df["club_share"] = df["actifs_qpv_in"] / df["actifs_qpv_allocated"]
    df["pop_share"] = df["qpv_population"] / df["population"]
    return df


def qpv_national(df: pd.DataFrame) -> dict[str, float]:
    """National shares from the département table (sums of numerators over sums of denominators)."""
    return {
        "lic_share": df["qpv_in"].sum() / df["qpv_allocated"].sum(),
        "club_share": df["actifs_qpv_in"].sum() / df["actifs_qpv_allocated"].sum(),
        "pop_share": df["qpv_population"].sum() / df["population"].sum(),
        "qpv_licences": float(df["qpv_in"].sum()),
        "qpv_clubs": float(df["actifs_qpv_in"].sum()),
        "qpv_population": float(df["qpv_population"].sum()),
    }


# --- Shares by département and by federation -----------------------------------------------------------------------
def departement_shares(lic_dep_fed: pd.DataFrame, pop_dep: pd.DataFrame, codes: list[str],
                       numerator: str, denominator: str) -> pd.DataFrame:
    """By département: numerator / denominator summed over the given federations (e.g. f / (f + h)).

    `denominator` may be a column name or 'f+h'. Share is NaN where the denominator is 0.
    """
    sub = lic_dep_fed[lic_dep_fed["code"].isin(codes)].assign(**{"f+h": lambda d: d["f"] + d["h"]})
    sums = sub.groupby("dep")[[numerator, denominator]].sum()
    df = pop_dep.set_index("dep").join(sums).fillna({numerator: 0, denominator: 0}).reset_index()
    df["share"] = (df[numerator] / df[denominator]).where(df[denominator] > 0)
    df["rank"] = df["share"].rank(ascending=False, method="min")
    return df.rename(columns={numerator: "num", denominator: "den"})


def women_by_federation(fed: pd.DataFrame, min_licences: int = 1_000) -> pd.DataFrame:
    """Federations with at least `min_licences` licences, ranked by women's share F / (F + H) (national, all places)."""
    df = fed[fed["lic_total"] >= min_licences].copy()
    df["share"] = df["lic_f"] / (df["lic_f"] + df["lic_h"])
    return df.sort_values("share").reset_index(drop=True)


def pyramid(pyr: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    """Licences by sex × age band for the given federations (age not reported kept in its own band 'NR')."""
    return (pyr[pyr["code"].isin(codes)].groupby(["sex", "age_band", "age_order"], as_index=False)["licences"].sum()
            .sort_values(["sex", "age_order"]))


def all_codes(fed: pd.DataFrame) -> list[str]:
    """Every federation that issued licences (national views: Women ranking, Explore)."""
    return fed.loc[fed["lic_total"] > 0, "code"].tolist()
