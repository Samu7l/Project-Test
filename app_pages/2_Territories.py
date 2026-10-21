"""Territories: licences per 10 000 inhabitants by département (map, overseas table, top/bottom 5) and by commune."""
import streamlit as st

from src import data, indicators, ui, viz

IDF_REGION = "11"  # Île-de-France: small départements, invisible at national scale → zoom map

fed = data.table("federations")
pop_dep = data.table("population_dep")
federation = st.session_state["federation"]
codes = indicators.selected_codes(fed, federation)
fed_label = ui.federation_label(federation)

rates = indicators.departement_rates(data.table("lic_dep_fed"), pop_dep, codes)
france = indicators.national_rate(rates)
mainland, overseas = rates[~rates["is_overseas"]], rates[rates["is_overseas"]]
top, bottom = mainland.iloc[0], mainland.iloc[-1]
z_range = (rates["rate"].min(), rates["rate"].max())  # one colour scale for all maps (overseas included)
MAYOTTE = "976"  # outside the geocoding scope: drawn in gray, no data
# The map column is ~730 px wide on a 1440 px laptop screen: 780 px = ~40 px title + ~670 px map + ~70 px colour bar,
# so the map area itself is roughly square.
MAIN_MAP_HEIGHT = 780

st.title("Territories")
st.markdown(
    f"For **{fed_label}**, France counts **{ui.fmt_rate(france)} {ui.RATE_UNIT}**. "
    f"In mainland France the rate ranges from {ui.fmt_rate(bottom['rate'])} in {bottom['dep_name']} "
    f"to {ui.fmt_rate(top['rate'])} in {top['dep_name']}."
)


def select_from_map(key: str) -> None:
    """Map click -> shared département. Runs as a callback, before the sidebar is drawn again."""
    points = st.session_state[key]["selection"]["points"]
    if not points:
        return
    point = points[0]
    dep = point.get("location") or (point.get("customdata") or [None] * 5)[4]
    if dep in set(pop_dep["dep"]):
        ui.select_departement(dep)


# --- Département map (mainland) + Île-de-France zoom --------------------------------------------------------------
geojson = data.departements_geojson()
selected = st.session_state["dep"]
col_map, col_zoom = st.columns([3, 1])
with col_map:
    st.plotly_chart(
        viz.departement_map(mainland, geojson, selected,
                            ui.contrast_title(top["dep_name"], top["rate"], bottom["dep_name"], bottom["rate"]),
                            z_range, height=MAIN_MAP_HEIGHT, scale_below=True),
        key="dep_map", on_select=lambda: select_from_map("dep_map"), selection_mode="points", width="stretch",
    )
with col_zoom:
    idf = mainland[mainland["reg"] == IDF_REGION]
    st.plotly_chart(
        viz.departement_map(idf, geojson, selected, "Zoom: Île-de-France", z_range, height=340, show_scale=False),
        key="idf_map", on_select=lambda: select_from_map("idf_map"), selection_mode="points", width="stretch",
    )
    below = (overseas["rate"] < france).sum()
    st.markdown(f"**Overseas: {below} of {len(overseas)} below the France average**")
    om_geojson = data.overseas_geojson()
    grid = st.columns(2)
    for i, row in enumerate(overseas.sort_values("dep").itertuples()):
        with grid[i % 2]:
            st.plotly_chart(
                viz.departement_map(overseas[overseas["dep"] == row.dep], om_geojson, selected,
                                    f"{row.dep_name}<br>{ui.fmt_rate(row.rate)}", z_range, height=170,
                                    show_scale=False),
                key=f"om_map_{row.dep}", on_select=lambda k=f"om_map_{row.dep}": select_from_map(k),
                selection_mode="points", width="stretch",
            )
    with grid[len(overseas) % 2]:
        st.plotly_chart(viz.no_data_map(om_geojson, MAYOTTE, "Mayotte<br>no data",
                                        "Mayotte: no data (outside the geocoding scope)", height=170),
                        width="stretch")
    st.caption("Same colour scale as the main map. Mayotte (gray) is outside the geocoding scope.")
ui.source_caption(ui.SOURCE_POPULATION, "Mainland France; click a département to select it (or use the sidebar).")

# --- Overseas table ---------------------------------------------------------------------------------------------
st.markdown("**Overseas départements** (rank among the 100 départements, 1 = highest rate)")
ui.table(overseas,
         {"dep": "Code", "dep_name": "Département", "licences": "Licences", "population": "Inhabitants",
          "rate": f"Licences per {ui.fmt_num(indicators.PER)} inh.", "rank": "Rank / 100"},
         {"licences": ui.fmt_num, "population": ui.fmt_num, "rate": ui.fmt_rate})
ui.source_caption(ui.SOURCE_POPULATION, "Mayotte is outside the geocoding scope.")

# --- Top / bottom 5 ---------------------------------------------------------------------------------------------
x_max = rates["rate"].max()
left, right = st.columns(2)
with left:
    st.plotly_chart(viz.rank_bars(rates.head(5), france, x_max, f"Top 5: {rates.iloc[0]['dep_name']} leads"),
                    width="stretch")
with right:
    st.plotly_chart(viz.rank_bars(rates.tail(5), france, x_max,
                                  f"Bottom 5: {rates.iloc[-1]['dep_name']} has the lowest rate"),
                    width="stretch")
ui.source_caption(ui.SOURCE_POPULATION,
                  "All 100 départements, overseas included. Same scale on both charts; dotted line: France average.")

# --- Commune drill-down -----------------------------------------------------------------------------------------
dep = st.session_state["dep"]
dep_row = rates.set_index("dep").loc[dep]
communes = indicators.commune_rates(data.table("lic_com_fed"), data.table("population_com"), codes, dep)
rated = communes[communes["above_threshold"]]

st.header(f"Inside {dep_row['dep_name']} ({dep})")
m1, m2, m3 = st.columns(3)
gap = dep_row["rate"] - france
delta, delta_format = ui.metric_delta(gap, dep_row["rate"])
m1.metric(ui.RATE_UNIT.capitalize(), ui.fmt_rate(dep_row["rate"]), delta=delta, format=delta_format,
          delta_description="vs France", delta_color="normal")
m2.metric("Rank among 100 départements", f"{dep_row['rank']} / 100")
m3.metric(f"Communes with ≥ {ui.MIN_POP_LABEL} inhabitants", f"{ui.fmt_num(len(rated))} / {ui.fmt_num(len(communes))}")

if rated.empty:
    title = f"No commune of {dep_row['dep_name']} reaches {ui.MIN_POP_LABEL} inhabitants"
else:
    best, worst = rated.iloc[0], rated.iloc[-1]
    title = (f"{best['com_name']} ({ui.fmt_rate(best['rate'])}) vs {worst['com_name']} "
             f"({ui.fmt_rate(worst['rate'])}) {ui.RATE_UNIT}")
st.plotly_chart(viz.commune_map(communes, data.communes_geojson(dep), title), width="stretch")
ui.source_caption(
    ui.SOURCE_POPULATION,
    f"Rates shown only for communes with at least {ui.MIN_POP_LABEL} inhabitants (gray: smaller communes, where a "
    "handful of licences gives extreme rates). Paris, Lyon and Marseille are shown as one commune.",
)
with st.expander(f"Table: communes of {dep_row['dep_name']}"):
    ui.table(communes,
             {"com": "Code", "com_name": "Commune", "population": "Inhabitants", "licences": "Licences",
              "rate": f"Licences per {ui.fmt_num(indicators.PER)} inh. (— below {ui.MIN_POP_LABEL} inh.)"},
             {"population": ui.fmt_num, "licences": ui.fmt_num, "rate": ui.fmt_rate})

with st.expander("Method"):
    excluded = fed[~fed["code"].isin(indicators.territory_codes(fed)) & (fed["lic_total"] > 0)]
    st.markdown(
        f"""
- **Rate** = licences ÷ legal population 2023 × {ui.fmt_num(indicators.PER)}, counted at the licence holder's
  **home** commune.
- **Excluded here** ({ui.fmt_num(excluded['lic_total'].sum())} licences): school sport (UNSS, USEP), recorded at
  the school's address, and Défense, Maccabi and Police, reported by département only. This keeps the
  département map and the commune view on the same licences.
- Only geocoded licences are mapped (mainland + overseas départements except Mayotte).
- A licence is not a person: one person can hold several licences.
"""
    )
