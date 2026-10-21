"""Seniors: licences of people aged 60+ per 10 000 inhabitants aged 60+, by département."""
import streamlit as st

from src import data, indicators, ui

SOURCE_CENSUS = "INSEE census 2023, population by sex and age"
UNIT_60 = f"licences per {ui.fmt_num(indicators.PER)} inhabitants aged 60+"

fed = data.table("federations")
federation = st.session_state["federation"]
codes = indicators.selected_codes(fed, federation)
fed_label = ui.federation_label(federation)
lic_dep_fed, pop_dep = data.table("lic_dep_fed"), data.table("population_dep")

rates = indicators.senior_rates(lic_dep_fed, pop_dep, data.table("population_sex_age"), codes)
france = indicators.national_rate(rates)
mainland = rates[~rates["is_overseas"]]
top, bottom = mainland.iloc[0], mainland.iloc[-1]

st.title("Seniors")
st.markdown(
    f"For **{fed_label}**, France counts **{ui.fmt_rate(france)} {UNIT_60}**. In mainland France the rate ranges "
    f"from {ui.fmt_rate(bottom['rate'])} in {bottom['dep_name']} to {ui.fmt_rate(top['rate'])} in {top['dep_name']}."
)

frame = rates.assign(
    value=rates["rate"], label=rates["rate"].map(ui.fmt_rate),
    hover="<b>" + rates["dep_name"] + "</b><br>" + rates["rate"].map(ui.fmt_rate) + f" {UNIT_60}<br>"
          + rates["licences"].map(ui.fmt_num) + " licences · " + rates["population"].map(ui.fmt_num)
          + " inhabitants aged 60+",
)
title = ui.contrast_title(top["dep_name"], top["rate"], bottom["dep_name"], bottom["rate"], "senior licence rate",
                          UNIT_60)
ui.france_maps(frame, title, key="seniors", colorbar_title=UNIT_60,
               overseas_heading=f"Overseas (France: {ui.fmt_rate(france)})")
ui.source_caption(SOURCE_CENSUS, f"{ui.first_upper(fed_label)}, without school sport (UNSS, USEP) and federations "
                  "reported by département only. Ages 60–99 in both the licences and the population.")

dep = st.session_state["dep"]
row = rates.set_index("dep").loc[dep]
m1, m2 = st.columns(2)
delta, fmt = ui.metric_delta(row["rate"] - france, ui.rate_decimals(row["rate"]))
m1.metric(f"{row['dep_name']}: {UNIT_60}", ui.fmt_rate(row["rate"]), delta=delta, format=fmt,
          delta_description="vs France")
m2.metric("Rank among 100 départements", f"{row['rank']} / 100")

with st.expander("Secondary view: share of licences held by people aged 60+"):
    shares = indicators.departement_shares(lic_dep_fed, pop_dep, codes, "age_60p", "age_known")
    share_fr = shares["num"].sum() / shares["den"].sum()
    st.markdown(
        f"This answers a different question: how old are the members? People aged 60+ hold "
        f"**{ui.fmt_pct(share_fr)}** of the licences of {fed_label} (licences with a known age). Unlike the rate "
        "above, this share also depends on how many young people play, and on each département's age structure."
    )
    ui.table(shares.sort_values("share", ascending=False),
             {"dep": "Code", "dep_name": "Département", "num": "Licences 60+", "den": "Licences (known age)",
              "share": "Share 60+"},
             {"num": ui.fmt_num, "den": ui.fmt_num, "share": ui.fmt_pct})

with st.expander("Table: rate by département"):
    ui.table(rates, {"dep": "Code", "dep_name": "Département", "licences": "Licences 60+",
                     "population": "Inhabitants aged 60+", "rate": UNIT_60, "rank": "Rank / 100"},
             {"licences": ui.fmt_num, "population": ui.fmt_num, "rate": ui.fmt_rate})
