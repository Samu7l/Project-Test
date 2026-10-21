"""Reusable Streamlit components: number formatting, sidebar filters, source captions, tables."""
from __future__ import annotations

from collections.abc import Callable

import pandas as pd
import streamlit as st

from src import data, indicators

SOURCE_LICENCES = ("Source: INJEP-MEDES, census of licences and clubs 2023, geocoded by INSEE (data.gouv.fr, "
                   "Licence Ouverte)")
SOURCE_POPULATION = "INSEE legal population 2023 (geo.api.gouv.fr)"
THOUSANDS = " "  # non-breaking space: "16 535 056" never wraps across two lines
NOT_APPLIED = "(filter not applied on this page)"


# --- Numbers --------------------------------------------------------------------------------------------------------
def fmt_num(x: float, decimals: int = 0) -> str:
    """The app's only number formatter: space as thousands separator, '.' as decimal mark.

    16535056 -> '16 535 056'; fmt_num(3.84, 1) -> '3.8'. Missing values -> '—'.
    """
    if pd.isna(x):
        return "—"
    return f"{x:,.{decimals}f}".replace(",", THOUSANDS)


def fmt_rate(x: float) -> str:
    """Rate per 10 000: no decimals from 100 up, one decimal below (small federations)."""
    return fmt_num(x, 0 if pd.isna(x) or x >= 100 else 1)


def fmt_pct(x: float, decimals: int = 1) -> str:
    """0.3865 -> '38.7 %'."""
    return f"{fmt_num(100 * x, decimals)} %"


def metric_delta(x: float, like: float) -> tuple[float, str]:
    """Numeric delta for st.metric and its printf format, with the same decimals as fmt_rate(like).

    st.metric needs a number to choose the arrow and colour (red ↓ when negative). Its formats cannot use a space
    as thousands separator, so this helper only accepts |x| < 1 000, where no separator is needed.
    """
    if abs(x) >= 1_000:
        raise ValueError(f"delta {x} needs a thousands separator: format it with fmt_num instead")
    if like >= 100:
        return int(round(x)), "%d"
    return round(x, 1), "%.1f"


RATE_UNIT = f"licences per {fmt_num(indicators.PER)} inhabitants"
MIN_POP_LABEL = fmt_num(indicators.MIN_COMMUNE_POP)


def contrast_title(high_name: str, high: float, low_name: str, low: float) -> str:
    """'A has 2.5× the licence rate of B', or a fallback when the lowest rate is zero."""
    if low == 0:
        return f"{high_name} has the highest rate ({fmt_rate(high)}); {low_name} has none"
    return f"{high_name} has {high / low:.1f}× the licence rate of {low_name}"


# --- Page elements --------------------------------------------------------------------------------------------------
def source_caption(*extra: str) -> None:
    """Source line under a chart."""
    st.caption(" · ".join([SOURCE_LICENCES, *extra]))


def table(df: pd.DataFrame, labels: dict[str, str], formats: dict[str, Callable[[float], str]]) -> None:
    """st.dataframe with French-style numbers: values are formatted for display but still sort as numbers."""
    st.dataframe(df[list(labels)].style.format(formats), hide_index=True, width="stretch",
                 column_config={col: label for col, label in labels.items()})


# --- Sidebar filters ------------------------------------------------------------------------------------------------
# The chosen values live in st.session_state["dep"] / ["federation"]. Widgets use separate keys
# ("dep_widget", ...) so that the value survives on pages where the widget is replaced by a disabled one.
def default_departement() -> str:
    """Default selection: the mainland département with the lowest rate (the story's starting point)."""
    fed = data.table("federations")
    rates = indicators.departement_rates(data.table("lic_dep_fed"), data.table("population_dep"),
                                         indicators.territory_codes(fed))
    return rates.loc[~rates["is_overseas"]].iloc[-1]["dep"]


def _copy_widget(name: str) -> None:
    """Widget callback: store the widget value as the shared filter value."""
    st.session_state[name] = st.session_state[f"{name}_widget"]


def _filter(name: str, label: str, options: dict[str, str], applies: bool, help_text: str) -> None:
    """One sidebar filter: an active selectbox, or a disabled one saying the filter is not applied."""
    if not applies:
        st.selectbox(label, [f"{options[st.session_state[name]]} {NOT_APPLIED}"], disabled=True,
                     key=f"{name}_off")
        return
    st.session_state[f"{name}_widget"] = st.session_state[name]  # sync (e.g. after a click on the map)
    st.selectbox(label, options=list(options), key=f"{name}_widget", format_func=options.get,
                 on_change=_copy_widget, args=(name,), help=help_text)


def sidebar(dep_applies: bool, federation_applies: bool) -> None:
    """Département selector and federation filter, shared by all pages."""
    deps = data.table("population_dep").sort_values("dep")
    fed = data.table("federations")
    in_scope = fed[fed["code"].isin(indicators.territory_codes(fed))].sort_values("name")

    st.session_state.setdefault("dep", default_departement())
    st.session_state.setdefault("federation", indicators.ALL)
    with st.sidebar:
        st.header("Filters")
        _filter("dep", "Département", {c: f"{c} – {n}" for c, n in zip(deps["dep"], deps["dep_name"])},
                dep_applies, "Also selectable by clicking the map on the Territories page.")
        _filter("federation", "Federation",
                {indicators.ALL: "All federations", **{c: f"{n} ({c})" for c, n in zip(in_scope["code"], in_scope["name"])}},
                federation_applies,
                "Federation names are kept in French, as in the source. School sport (UNSS, USEP) and federations "
                "reported by département only are not listed: they are excluded from territorial views.")
        st.caption("Your choices are kept when you change page.")


def select_departement(dep: str) -> None:
    """Set the shared département (used by map clicks)."""
    st.session_state["dep"] = dep


def federation_label(code: str) -> str:
    """'all federations' or the French federation name."""
    if code == indicators.ALL:
        return "all federations"
    return data.table("federations").set_index("code").loc[code, "name"]
