"""The limits of the analysis, as shown on the Data & Limits page. Numbers are computed from the processed tables.

This is the reference version of docs/data_audit.md §11.
"""
from __future__ import annotations

import pandas as pd

from src import ui


def limits(fed: pd.DataFrame, rates: pd.DataFrame, validation: pd.DataFrame) -> list[tuple[str, str]]:
    """(topic, text) pairs. `rates` = departement_rates for the territorial scope; `validation` = validation table."""
    school = fed.loc[fed["is_club_address"], "lic_total"].sum()
    dept_only = fed.loc[fed["is_dept_only"], "lic_total"].sum()
    geocoded = fed["lic_geocoded"].sum() / fed["lic_total"].sum()
    disability = fed[fed["is_disability"]]
    revised = validation.loc[validation["check"].str.startswith("Gap vs first publication"), "observed"]
    dep_gap = validation.loc[validation["check"].str.startswith("Département totals vs INJEP"), "observed"]
    return [
        ("Licences, not people", "A licence is not a person: one person can hold several licences in different "
         "federations. All figures count licences."),
        ("School sport", f"UNSS and USEP ({ui.fmt_num(school)} licences) are left out of every map and territorial "
         "indicator: their licences are recorded at the school's address, not where the pupil lives, so they would "
         "distort comparisons between places. They are kept in the national total, the women's ranking and Explore."),
        ("Département-only federations", f"Défense, Maccabi and Police ({ui.fmt_num(dept_only)} licences) report "
         "by département only, with no commune or QPV: they are left out of all territorial views (so that "
         "département and commune views count the same licences) and kept in national totals."),
        ("Geocoding", f"Maps use geocoded licences ({ui.fmt_pct(geocoded, 2)}). Licences held abroad, in Mayotte, in "
         f"overseas collectivities or not allocated ({ui.fmt_pct(1 - geocoded, 2)}) are in the national total only."),
        ("Overseas", "Guadeloupe, Martinique, Guyane and La Réunion are shown in small maps next to the main map, on "
         "the same colour scale. Mayotte is outside the geocoding scope (gray, no data)."),
        ("Small numbers", f"Commune rates are shown only from {ui.MIN_POP_LABEL} inhabitants; Paris, Lyon and "
         "Marseille are shown as single communes."),
        ("Population", "INSEE legal population 2023 (population municipale), geography COG 2026; licence communes "
         "(COG 2024) are mapped to current communes."),
        ("QPV", "2024 QPV list. Benchmark = INSEE QPV population (1/1/2020 mainland, 1/1/2021 overseas) ÷ legal "
         "population 2023: the dates differ by about three years. Shares only; a club located in a QPV can serve "
         "people who live elsewhere. QPV residents are younger than average, so the licence gap is probably "
         "understated (see Implications)."),
        ("Women", "Shares = women ÷ (women + men); sex is reported for every licence. The federation ranking is "
         "national (all places, school sport included); the football map uses geocoded licences."),
        ("Seniors", "The share of licences held by people aged 60+ partly reflects each département's age "
         "structure: it is not a participation rate. The legal-population file has no sex or age; the INSEE census "
         "2023 table by sex and age (same year) has been identified to compute rates per 10 000 people aged 60+ "
         "and per 10 000 women / men, but is not used yet."),
        ("Disability", f"Only {' and '.join(disability['name'])}: a lower bound, as many disabled athletes hold "
         "ordinary licences and the census does not record disability. No disabled population by département: "
         "never a share of disabled people. The map's colour scale is capped at the second-highest département; "
         "the link with medico-social establishments (DREES) is a hypothesis."),
        ("Published figures", f"Our national figures equal INJEP's revised 2023 results (July 2025); gap with the "
         f"first publication: {revised.iloc[0] if len(revised) else '—'}. Département totals differ slightly from "
         f"INJEP's tables, which re-allocate non-response (largest gap {dep_gap.iloc[0] if len(dep_gap) else '—'})."),
        ("Single year", "2023 only: no trend can be read from this app."),
    ]
