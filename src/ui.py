"""Reusable Streamlit components: sidebar filters, number formatting, source captions."""
from __future__ import annotations

import streamlit as st

from src import data, indicators

SOURCE_LICENCES = ("Source: INJEP-MEDES, census of licences and clubs 2023, geocoded by INSEE (data.gouv.fr, "
                   "Licence Ouverte)")
SOURCE_POPULATION = "INSEE legal population 2023 (geo.api.gouv.fr)"


def fmt_int(n: float) -> str:
    """16535056 -> '16,535,056'."""
    return f"{n:,.0f}"


def fmt_rate(x: float) -> str:
    """Rate per 10,000: no decimals from 100 up, one decimal below (small federations)."""
    return f"{x:,.0f}" if x >= 100 else f"{x:,.1f}"


def contrast_title(high_name: str, high: float, low_name: str, low: float) -> str:
    """'A has 2.5× the licence rate of B', or a fallback when the lowest rate is zero."""
    if low == 0:
        return f"{high_name} has the highest rate ({fmt_rate(high)}); {low_name} has none"
    return f"{high_name} has {high / low:.1f}× the licence rate of {low_name}"


def fmt_pct(x: float, decimals: int = 1) -> str:
    """0.3865 -> '38.7 %'."""
    return f"{100 * x:.{decimals}f} %"


def source_caption(*extra: str) -> None:
    """Source line under a chart."""
    st.caption(" · ".join([SOURCE_LICENCES, *extra]))


def default_departement() -> str:
    """Default selection: the mainland département with the lowest rate (the story's starting point)."""
    fed = data.table("federations")
    rates = indicators.departement_rates(data.table("lic_dep_fed"), data.table("population_dep"),
                                         indicators.territory_codes(fed))
    return rates.loc[~rates["is_overseas"]].iloc[-1]["dep"]


def sidebar() -> None:
    """Département selector and federation filter, stored in st.session_state['dep'] / ['federation']."""
    deps = data.table("population_dep").sort_values("dep")
    dep_names = dict(zip(deps["dep"], deps["dep_name"]))
    fed = data.table("federations")
    in_scope = fed[fed["code"].isin(indicators.territory_codes(fed))].sort_values("name")
    fed_names = dict(zip(in_scope["code"], in_scope["name"]))

    st.session_state.setdefault("dep", default_departement())
    st.session_state.setdefault("federation", indicators.ALL)
    with st.sidebar:
        st.header("Filters")
        st.selectbox("Département", options=list(dep_names), key="dep",
                     format_func=lambda c: f"{c} – {dep_names[c]}")
        st.selectbox("Federation", options=[indicators.ALL, *fed_names], key="federation",
                     format_func=lambda c: "All federations" if c == indicators.ALL else f"{fed_names[c]} ({c})",
                     help="Applies to the Territories page. Federation names are kept in French, as in the source. "
                          "School sport (UNSS, USEP) and federations reported by département only are not listed: "
                          "they are excluded from territorial views.")
        st.caption("Filters are shared by all pages.")


def federation_label(code: str) -> str:
    """'All federations' or the French federation name."""
    if code == indicators.ALL:
        return "all federations"
    fed = data.table("federations").set_index("code")
    return fed.loc[code, "name"]
