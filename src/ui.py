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


def metric_delta(x: float, decimals: int) -> tuple[float, str]:
    """Numeric delta for st.metric and its printf format.

    st.metric needs a number to choose the arrow and colour (red ↓ when negative). Its formats cannot use a space
    as thousands separator, so this helper only accepts |x| < 1 000, where no separator is needed.
    """
    if abs(x) >= 1_000:
        raise ValueError(f"delta {x} needs a thousands separator: format it with fmt_num instead")
    if decimals == 0:
        return int(round(x)), "%d"
    return round(x, decimals), f"%.{decimals}f"


def rate_decimals(x: float) -> int:
    """Decimals used by fmt_rate for this value (0 from 100 up, 1 below)."""
    return 0 if x >= 100 else 1


RATE_UNIT = f"licences per {fmt_num(indicators.PER)} inhabitants"
MIN_POP_LABEL = fmt_num(indicators.MIN_COMMUNE_POP)


def contrast_title(high_name: str, high: float, low_name: str, low: float, measure: str = "licence rate",
                   unit: str | None = None) -> str:
    """'A has 2.5× the licence rate of B'.

    When the lowest rate is zero or tiny (ratio > 10, e.g. a handful of licences), a ratio would mislead:
    the title gives the range instead (with `unit`, default RATE_UNIT).
    """
    if low == 0 or high / low > 10:
        return f"From {fmt_rate(low)} in {low_name} to {fmt_rate(high)} in {high_name} ({unit or RATE_UNIT})"
    return f"{high_name} has {fmt_num(high / low, 1)}× the {measure} of {low_name}"


def first_upper(text: str) -> str:
    """Capitalise the first letter only ('all federations' -> 'All federations'; 'FF de Football' unchanged).

    str.capitalize() would lowercase the rest ('Ff de football').
    """
    return text[:1].upper() + text[1:]


def age_label(band: str) -> str:
    """Census age band in English: '10 à 14 ans' -> '10–14'; 'NR' -> 'age not reported'."""
    if band == "NR":
        return "age not reported"
    return band.replace(" ans", "").replace(" à ", "–")


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


def _filter(name: str, label: str, labels: dict[str, str], options: list[str], applies: bool,
            help_text: str) -> None:
    """One sidebar filter: an active selectbox over `options`, or a disabled one saying it is not applied.

    `labels` names every possible value (so the disabled box can show the current one).
    """
    if not applies:
        st.selectbox(label, [f"{labels[st.session_state[name]]} {NOT_APPLIED}"], disabled=True, key=f"{name}_off")
        return
    if st.session_state[name] not in options:  # e.g. UNSS chosen on Explore, not offered on geographic pages
        st.toast(f"{labels[st.session_state[name]]} is not available on this page: showing {labels[options[0]]}.")
        st.session_state[name] = options[0]
    st.session_state[f"{name}_widget"] = st.session_state[name]  # sync (e.g. after a click on the map)
    st.selectbox(label, options=options, key=f"{name}_widget", format_func=labels.get,
                 on_change=_copy_widget, args=(name,), help=help_text)


GEO_SCOPE, NATIONAL_SCOPE = "geo", "national"


def sidebar(dep_applies: bool, federation_applies: bool, federation_scope: str = GEO_SCOPE) -> None:
    """Département selector and federation filter, shared by all pages.

    federation_scope: GEO_SCOPE lists the federations used in territorial views (no school sport, no
    département-only federations); NATIONAL_SCOPE lists every federation with licences.
    """
    deps = data.table("population_dep").sort_values("dep")
    fed = data.table("federations").sort_values("name")
    fed_labels = {indicators.ALL: "All federations", **{c: f"{n} ({c})" for c, n in zip(fed["code"], fed["name"])}}
    scope = indicators.territory_codes(fed) if federation_scope == GEO_SCOPE else indicators.all_codes(fed)
    fed_options = [indicators.ALL, *[c for c in fed["code"] if c in set(scope)]]
    help_fed = ("Federation names are kept in French, as in the source. "
                + ("School sport (UNSS, USEP) and federations reported by département only are not listed on this "
                   "page: they are excluded from territorial views." if federation_scope == GEO_SCOPE
                   else "All federations are listed on this page (national view)."))

    st.session_state.setdefault("dep", default_departement())
    st.session_state.setdefault("federation", indicators.ALL)
    with st.sidebar:
        st.header("Filters")
        dep_labels = {c: f"{c} – {n}" for c, n in zip(deps["dep"], deps["dep_name"])}
        _filter("dep", "Département", dep_labels, list(dep_labels), dep_applies,
                "Also selectable by clicking a map.")
        _filter("federation", "Federation", fed_labels, fed_options, federation_applies, help_fed)
        st.caption("Your choices are kept when you change page.")


def select_departement(dep: str) -> None:
    """Set the shared département (used by map clicks)."""
    st.session_state["dep"] = dep


def pick_from_map(key: str) -> None:
    """Map click callback: the clicked département becomes the shared selection (customdata[1] = code)."""
    points = st.session_state[key]["selection"]["points"]
    if not points:
        return
    point = points[0]
    dep = point.get("location") or (point.get("customdata") or [None, None])[1]
    if dep in set(data.table("population_dep")["dep"]):
        select_departement(dep)


IDF_REGION = "11"  # Île-de-France: small départements, invisible at national scale → zoom map
MAYOTTE = "976"    # outside the geocoding scope: drawn in gray, no data
# The map column is ~730 px wide on a 1440 px laptop screen: 780 px = ~40 px title + ~670 px map + ~70 px colour bar,
# so the map area itself is roughly square.
MAIN_MAP_HEIGHT = 780


def france_maps(frame: pd.DataFrame, title: str, key: str, colorbar_title: str, overseas_heading: str,
                tick_suffix: str = "", z_max: float | None = None) -> None:
    """Main mainland map + Île-de-France zoom + overseas maps (and Mayotte, no data), all on one colour scale.

    `frame`: one row per département with dep, dep_name, reg, is_overseas, value (colour; NaN = no value),
    label (short text under each overseas name) and hover (full hover text). Every map is clickable.
    `z_max` caps the colour scale (an outlier would otherwise wash out every other département); values above it
    get the darkest colour, and the page must say so in its caption.
    """
    from src import viz  # local import: viz imports ui

    selected = st.session_state["dep"]
    valid = frame.dropna(subset=["value"])
    z_range = (valid["value"].min(), valid["value"].max() if z_max is None else z_max)
    geojson, om_geojson = data.departements_geojson(), data.overseas_geojson()
    mainland, overseas = frame[~frame["is_overseas"]], frame[frame["is_overseas"]].sort_values("dep")

    col_map, col_zoom = st.columns([3, 1])
    with col_map:
        st.plotly_chart(
            viz.departement_map(mainland, geojson, selected, title, z_range, colorbar_title, tick_suffix,
                                height=MAIN_MAP_HEIGHT, scale_below=True),
            key=f"{key}_main", on_select=lambda: pick_from_map(f"{key}_main"), selection_mode="points",
            width="stretch")
    with col_zoom:
        st.plotly_chart(
            viz.departement_map(mainland[mainland["reg"] == IDF_REGION], geojson, selected, "Zoom: Île-de-France",
                                z_range, height=340, show_scale=False),
            key=f"{key}_idf", on_select=lambda: pick_from_map(f"{key}_idf"), selection_mode="points",
            width="stretch")
        st.markdown(f"**{overseas_heading}**")
        grid = st.columns(2)
        for i, row in enumerate(overseas.itertuples()):
            with grid[i % 2]:
                k = f"{key}_om_{row.dep}"
                st.plotly_chart(
                    viz.departement_map(overseas[overseas["dep"] == row.dep], om_geojson, selected,
                                        f"{row.dep_name}<br>{row.label}", z_range, height=170, show_scale=False),
                    key=k, on_select=lambda k=k: pick_from_map(k), selection_mode="points", width="stretch")
        with grid[len(overseas) % 2]:
            st.plotly_chart(viz.no_data_map(om_geojson, MAYOTTE, "Mayotte<br>no data",
                                            "Mayotte: no data (outside the geocoding scope)", height=170),
                            key=f"{key}_om_976", width="stretch")
        st.caption("Same colour scale as the main map. Mayotte (gray) is outside the geocoding scope.")


def rate_frame(rates: pd.DataFrame) -> pd.DataFrame:
    """Map frame for licence rates (output of indicators.departement_rates): value, label, hover."""
    return rates.assign(
        value=rates["rate"], label=rates["rate"].map(fmt_rate),
        hover=("<b>" + rates["dep_name"] + "</b><br>" + rates["rate"].map(fmt_rate) + f" {RATE_UNIT}<br>"
               + rates["licences"].map(fmt_num) + " licences · " + rates["population"].map(fmt_num)
               + " inhabitants"),
    )


def federation_label(code: str) -> str:
    """'all federations' or the French federation name."""
    if code == indicators.ALL:
        return "all federations"
    return data.table("federations").set_index("code").loc[code, "name"]
