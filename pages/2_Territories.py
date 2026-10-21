"""Territories: licences per 10,000 inhabitants by département (map, overseas table, top/bottom 5) and by commune."""
import streamlit as st

from src import data, indicators, ui, viz

fed = data.table("federations")
pop_dep = data.table("population_dep")
federation = st.session_state["federation"]
codes = indicators.selected_codes(fed, federation)
fed_label = ui.federation_label(federation)

rates = indicators.departement_rates(data.table("lic_dep_fed"), pop_dep, codes)
france = indicators.national_rate(rates)
mainland, overseas = rates[~rates["is_overseas"]], rates[rates["is_overseas"]]
top, bottom = mainland.iloc[0], mainland.iloc[-1]

st.title("Territories")
st.markdown(
    f"For **{fed_label}**, France counts **{ui.fmt_rate(france)} licences per 10,000 inhabitants**. "
    f"In mainland France the rate ranges from {ui.fmt_rate(bottom['rate'])} in {bottom['dep_name']} "
    f"to {ui.fmt_rate(top['rate'])} in {top['dep_name']}."
)


def select_from_map() -> None:
    """Map click -> sidebar département. Runs as a callback, before the sidebar widget is drawn again."""
    points = st.session_state["dep_map"]["selection"]["points"]
    if not points:
        return
    point = points[0]
    dep = point.get("location") or (point.get("customdata") or [None])[0]
    if dep is None and "point_index" in point:
        dep = mainland.iloc[point["point_index"]]["dep"]
    if dep in set(pop_dep["dep"]):
        st.session_state["dep"] = dep


# --- Département map (mainland) -------------------------------------------------------------------------------
st.plotly_chart(
    viz.departement_map(mainland, data.departements_geojson(), st.session_state["dep"],
                        ui.contrast_title(top["dep_name"], top["rate"], bottom["dep_name"], bottom["rate"])),
    key="dep_map", on_select=select_from_map, selection_mode="points", width="stretch",
)
ui.source_caption(ui.SOURCE_POPULATION, "Mainland France; click a département to select it (or use the sidebar).")

# --- Overseas table ---------------------------------------------------------------------------------------------
st.markdown(f"**Overseas départements** (rank among the 100 départements, 1 = highest rate)")
st.dataframe(
    overseas[["dep", "dep_name", "licences", "population", "rate", "rank"]],
    hide_index=True, width="stretch",
    column_config={
        "dep": "Code", "dep_name": "Département",
        "licences": st.column_config.NumberColumn("Licences", format="localized"),
        "population": st.column_config.NumberColumn("Inhabitants", format="localized"),
        "rate": st.column_config.NumberColumn("Licences per 10,000 inh.", format="%.1f"),
        "rank": st.column_config.NumberColumn("Rank / 100"),
    },
)
ui.source_caption(ui.SOURCE_POPULATION, "Mayotte is outside the geocoding scope.")

# --- Top / bottom 5 ---------------------------------------------------------------------------------------------
left, right = st.columns(2)
with left:
    st.plotly_chart(viz.rank_bars(rates.head(5), france, rates["rate"].max(), f"Top 5: {rates.iloc[0]['dep_name']} leads"),
                    width="stretch")
with right:
    st.plotly_chart(viz.rank_bars(rates.tail(5), france, rates["rate"].max(),
                                  f"Bottom 5: {rates.iloc[-1]['dep_name']} has the lowest rate"),
                    width="stretch")
ui.source_caption(ui.SOURCE_POPULATION, "All 100 départements, overseas included. Same scale on both charts; dotted line: France average.")

# --- Commune drill-down -----------------------------------------------------------------------------------------
dep = st.session_state["dep"]
dep_row = rates.set_index("dep").loc[dep]
communes = indicators.commune_rates(data.table("lic_com_fed"), data.table("population_com"), codes, dep)
rated = communes[communes["above_threshold"]]

st.header(f"Inside {dep_row['dep_name']} ({dep})")
m1, m2, m3 = st.columns(3)
m1.metric("Licences per 10,000 inhabitants", ui.fmt_rate(dep_row["rate"]),
          delta=f"{'+' if dep_row['rate'] >= france else '−'}{ui.fmt_rate(abs(dep_row['rate'] - france))} vs France",
          delta_color="normal")
m2.metric("Rank among 100 départements", f"{dep_row['rank']} / 100")
m3.metric(f"Communes with ≥ {indicators.MIN_COMMUNE_POP:,} inhabitants", f"{len(rated)} / {len(communes)}")

if rated.empty:
    title = f"No commune of {dep_row['dep_name']} reaches {indicators.MIN_COMMUNE_POP:,} inhabitants"
else:
    best, worst = rated.iloc[0], rated.iloc[-1]
    title = (f"{best['com_name']} ({ui.fmt_rate(best['rate'])}) vs {worst['com_name']} "
             f"({ui.fmt_rate(worst['rate'])}) licences per 10,000 inhabitants")
st.plotly_chart(viz.commune_map(communes, data.communes_geojson(dep), indicators.MIN_COMMUNE_POP, title),
                width="stretch")
ui.source_caption(
    ui.SOURCE_POPULATION,
    f"Rates shown only for communes with at least {indicators.MIN_COMMUNE_POP:,} inhabitants (gray: smaller "
    "communes, where a handful of licences gives extreme rates). Paris, Lyon and Marseille are shown as one commune.",
)
with st.expander(f"Table: communes of {dep_row['dep_name']}"):
    st.dataframe(
        communes[["com", "com_name", "population", "licences", "rate"]], hide_index=True, width="stretch",
        column_config={
            "com": "Code", "com_name": "Commune",
            "population": st.column_config.NumberColumn("Inhabitants", format="localized"),
            "licences": st.column_config.NumberColumn("Licences", format="localized"),
            "rate": st.column_config.NumberColumn("Licences per 10,000 inh.", format="%.1f",
                                                  help=f"Empty below {indicators.MIN_COMMUNE_POP:,} inhabitants"),
        },
    )

with st.expander("Method"):
    excluded = fed[~fed["code"].isin(indicators.territory_codes(fed)) & (fed["lic_total"] > 0)]
    st.markdown(
        f"""
- **Rate** = licences ÷ legal population 2023 × 10,000, counted at the licence holder's **home** commune.
- **Excluded here** ({ui.fmt_int(excluded['lic_total'].sum())} licences): school sport (UNSS, USEP), recorded at
  the school's address, and Défense, Maccabi and Police, reported by département only. This keeps the
  département map and the commune view on the same licences.
- Only geocoded licences are mapped (mainland + overseas départements except Mayotte).
- A licence is not a person: one person can hold several licences.
"""
    )
