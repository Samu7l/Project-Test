"""Priority neighbourhoods (QPV): licences of QPV residents and clubs located in QPV, against the QPV population share."""
import streamlit as st

from src import data, indicators, ui, viz

SOURCE_QPV = "INSEE, population of the 2024 QPV (pop. 2020 mainland, 2021 overseas)"

fed = data.table("federations")
federation = st.session_state["federation"]
codes = indicators.selected_codes(fed, federation)
fed_label = ui.federation_label(federation)

q = indicators.qpv_shares(data.table("lic_dep_fed"), data.table("clubs_dep_fed"), data.table("population_dep"),
                          data.table("population_qpv"), codes)
nat = indicators.qpv_national(q)
q["hover"] = ("<b>" + q["dep_name"] + "</b><br>Population in QPV: " + q["pop_share"].map(ui.fmt_pct)
              + "<br>Licences of QPV residents: " + q["lic_share"].map(ui.fmt_pct)
              + "<br>Clubs and EPA in QPV: " + q["club_share"].map(ui.fmt_pct))

st.title("Priority neighbourhoods (QPV)")
st.markdown(
    f"QPV residents make up **{ui.fmt_pct(nat['pop_share'])}** of the population but hold **"
    f"{ui.fmt_pct(nat['lic_share'])}** of the licences of {fed_label}: about **{nat['lic_share'] / nat['pop_share']:.2f}** "
    f"of their population share. Only **{ui.fmt_pct(nat['club_share'])}** of active clubs and EPA are located in a QPV."
)

c1, c2, c3 = st.columns(3)
c1.metric("Population living in a QPV", ui.fmt_pct(nat["pop_share"]),
          help=f"{ui.fmt_num(nat['qpv_population'])} inhabitants in the 2024 QPV (INSEE), divided by the legal "
               "population 2023 of the 100 départements.")
for col, label, share, help_text in [
    (c2, "Licences held by QPV residents", nat["lic_share"],
     f"{ui.fmt_num(nat['qpv_licences'])} licences whose holder lives in a QPV, out of licences with a known QPV status."),
    (c3, "Active clubs and EPA located in a QPV", nat["club_share"],
     f"{ui.fmt_num(nat['qpv_clubs'])} active clubs and EPA located in a QPV. A club in a QPV can also serve people "
     "who live elsewhere."),
]:
    delta, fmt = ui.metric_delta((share - nat["pop_share"]) * 100, 1)
    col.metric(label, ui.fmt_pct(share), delta=delta, format=fmt, delta_description="pts vs population share",
               help=help_text)
ui.source_caption(SOURCE_QPV, ui.SOURCE_POPULATION)

# --- Scatter: every département against parity --------------------------------------------------------------------
dep = st.session_state["dep"]
with_qpv = q[q["pop_share"] > 0]
left, right = st.columns(2)
for col, share_col, what, y_label in [
    (left, "lic_share", "Licences", "share of licences held by QPV residents (%)"),
    (right, "club_share", "Clubs and EPA", "share of active clubs and EPA located in a QPV (%)"),
]:
    below = (with_qpv[share_col] < with_qpv["pop_share"]).sum()
    with col:
        st.plotly_chart(viz.qpv_scatter(with_qpv, share_col, dep,
                                        f"{what}: {below} of {len(with_qpv)} départements below parity",
                                        y_label), width="stretch")
ui.source_caption(SOURCE_QPV, "Each dot is a département; below the dashed line, QPV residents (or clubs) are "
                              "under-represented compared with the QPV share of the population.")

# --- Selected département -----------------------------------------------------------------------------------------
row = q.set_index("dep").loc[dep]
st.header(f"{row['dep_name']} ({dep})")
if row["pop_share"] == 0:
    st.info(f"{row['dep_name']} has no priority neighbourhood (QPV).")
else:
    m1, m2, m3 = st.columns(3)
    m1.metric("Population living in a QPV", ui.fmt_pct(row["pop_share"]))
    for col, label, share in [(m2, "Licences held by QPV residents", row["lic_share"]),
                              (m3, "Active clubs and EPA located in a QPV", row["club_share"])]:
        delta, fmt = ui.metric_delta((share - row["pop_share"]) * 100, 1)
        col.metric(label, ui.fmt_pct(share), delta=delta, format=fmt, delta_description="pts vs population share")

with st.expander("Table: all départements"):
    ui.table(q.sort_values("pop_share", ascending=False),
             {"dep": "Code", "dep_name": "Département", "pop_share": "Population in QPV",
              "lic_share": "Licences of QPV residents", "club_share": "Clubs and EPA in QPV",
              "qpv_in": "Licences of QPV residents (n)", "actifs_qpv_in": "Clubs and EPA in QPV (n)"},
             {"pop_share": ui.fmt_pct, "lic_share": ui.fmt_pct, "club_share": ui.fmt_pct, "qpv_in": ui.fmt_num,
              "actifs_qpv_in": ui.fmt_num})

with st.expander("Method"):
    st.markdown(
        f"""
- **Licences of QPV residents**: licences whose holder lives in a 2024 QPV (code `QN…` in the census), divided by
  all licences with a known QPV status. Licences are counted at the holder's **home**.
- **Clubs and EPA in QPV**: active structures located in a QPV, divided by active structures with a known status.
  A club located in a QPV may also welcome people who live elsewhere, and the other way round.
- **Benchmark**: population of the 2024 QPV (INSEE, municipal population at 1 January 2020 in mainland France,
  2021 overseas) divided by the legal population 2023. The two dates differ by about three years; the effect on
  a share is small.
- **Excluded**: school sport (UNSS, USEP), recorded at the school, and Défense, Maccabi and Police, which give no
  QPV information. All {ui.fmt_num(len(data.table('population_qpv')))} QPV of the study area have at least one
  licence.
- Shares only: the census gives no QPV population by age or sex.
"""
    )
