"""Explore: age pyramid (women left, men right) for the federation chosen in the sidebar."""
import streamlit as st

from src import data, indicators, ui, viz

fed = data.table("federations")
federation = st.session_state["federation"]
codes = indicators.all_codes(fed) if federation == indicators.ALL else [federation]
fed_label = ui.federation_label(federation)

pyr = indicators.pyramid(data.table("pyramid"), codes)
known = pyr[pyr["age_band"] != "NR"]
age_nr = pyr.loc[pyr["age_band"] == "NR", "licences"].sum()
total = pyr["licences"].sum()
women = pyr.loc[pyr["sex"] == "F", "licences"].sum()
under_20 = known.loc[known["age_order"] <= 3, "licences"].sum()        # bands 1-4 … 15-19
over_60 = known.loc[known["age_band"].isin(["60 à 64 ans", "65 à 69 ans", "70 à 74 ans", "75 à 79 ans",
                                            "80 à 99 ans"]), "licences"].sum()
peak = known.loc[known["licences"].idxmax()]

st.title("Explore")
st.markdown(f"Age and sex profile of the licences of **{fed_label}**. Choose a federation in the sidebar "
            "(every federation is listed here, school sport included).")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Licences", ui.fmt_num(total), help="All places (national view).")
c2.metric("Held by women", ui.fmt_pct(women / total) if total else "—")
c3.metric("Aged under 20", ui.fmt_pct(under_20 / known["licences"].sum()) if total else "—",
          help="Share of licences with a known age.")
c4.metric("Aged 60 and over", ui.fmt_pct(over_60 / known["licences"].sum()) if total else "—",
          help="Share of licences with a known age.")

sex_name = {"F": "women", "H": "men"}[peak["sex"]]
st.plotly_chart(viz.pyramid(known, f"The largest group: {sex_name} aged {ui.age_label(peak['age_band'])} "
                                   f"({ui.fmt_num(peak['licences'])} licences)"), width="stretch")
ui.source_caption(f"{fed_label.capitalize()}, all places. Age bands as in the census (1–4, then 5-year bands, "
                  f"80–99). Licences with no age reported: {ui.fmt_num(age_nr)} (not shown).")
