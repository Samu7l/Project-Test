"""Implications: one takeaway per page, where public effort could be targeted, and what the data cannot say."""
import streamlit as st

from src import data, indicators, ui
from src.sources import registry

FOOTBALL = "111"

fed = data.table("federations")
lic_dep_fed, pop_dep = data.table("lic_dep_fed"), data.table("population_dep")
geo_codes = indicators.territory_codes(fed)

# Territories
rates = indicators.departement_rates(lic_dep_fed, pop_dep, geo_codes)
france = indicators.national_rate(rates)
mainland, overseas = rates[~rates["is_overseas"]], rates[rates["is_overseas"]]
top, bottom = mainland.iloc[0], mainland.iloc[-1]
overseas_below = int((overseas["rate"] < france).sum())
# QPV
qpv = indicators.qpv_shares(lic_dep_fed, data.table("clubs_dep_fed"), pop_dep, data.table("population_qpv"), geo_codes)
nat_qpv = indicators.qpv_national(qpv)
qpv_bottom = qpv.set_index("dep").loc[bottom["dep"]]
# Women
summary = indicators.national_summary(fed)
foot = fed.set_index("code").loc[FOOTBALL]
foot_share = foot["lic_f"] / (foot["lic_f"] + foot["lic_h"])
foot_dep = indicators.departement_shares(lic_dep_fed, pop_dep, [FOOTBALL], "f", "f+h")
foot_low = foot_dep[~foot_dep["is_overseas"]].nsmallest(3, "share")
# Seniors
seniors = indicators.departement_shares(lic_dep_fed, pop_dep, geo_codes, "age_60p", "age_known")
senior_share = seniors["num"].sum() / seniors["den"].sum()
sen_main = seniors[~seniors["is_overseas"]].sort_values("share")
# Disability
dis_codes = fed.loc[fed["is_disability"], "code"].tolist()
dis = indicators.departement_rates(lic_dep_fed, pop_dep, dis_codes)
dis_france = indicators.national_rate(dis)
# Age profile of all licences (for the QPV caveat)
pyr = indicators.pyramid(data.table("pyramid"), indicators.all_codes(fed))
known = pyr[pyr["age_band"] != "NR"]
under_20 = known.loc[known["age_order"] <= 3, "licences"].sum() / known["licences"].sum()

st.title("Implications")
st.markdown("What the 2023 census shows, where public effort could be targeted, and what it cannot tell us.")

st.header("Five takeaways")
st.markdown(
    f"""
1. **Territories** — In mainland France, {top['dep_name']} counts {ui.fmt_rate(top['rate'])} licences per
   {ui.fmt_num(indicators.PER)} inhabitants, **{ui.fmt_num(top['rate'] / bottom['rate'], 1)} times**
   {bottom['dep_name']} ({ui.fmt_rate(bottom['rate'])}); {overseas_below} of {len(overseas)} overseas départements are
   below the France average ({ui.fmt_rate(france)}).
2. **Priority neighbourhoods** — QPV residents are {ui.fmt_pct(nat_qpv['pop_share'])} of the population but hold
   **{ui.fmt_pct(nat_qpv['lic_share'])}** of licences; {ui.fmt_pct(nat_qpv['club_share'])} of active clubs and EPA are
   located in a QPV.
3. **Women** — Women hold {ui.fmt_pct(summary.women_share)} of all licences and only **{ui.fmt_pct(foot_share)}** in
   football, the largest federation.
4. **Seniors** — People aged 60+ hold {ui.fmt_pct(senior_share)} of licences, from {ui.fmt_pct(sen_main.iloc[0]['share'])}
   in {sen_main.iloc[0]['dep_name']} to {ui.fmt_pct(sen_main.iloc[-1]['share'])} in {sen_main.iloc[-1]['dep_name']}
   (a share that partly reflects each département's age structure).
5. **Disability** — The two disability federations count **{ui.fmt_rate(dis_france)}** licences per
   {ui.fmt_num(indicators.PER)} inhabitants, a lower bound of disabled people's organised sport.
"""
)

st.header("Where public effort could be targeted")
st.markdown(
    f"""
- **Priority neighbourhoods.** The data suggests that QPV residents hold about **{ui.fmt_num(nat_qpv['lic_share'] /
  nat_qpv['pop_share'], 2)}** of the licences their population share would imply, and clubs are rarer there.
  Club creation or support for existing clubs in or near QPV may be a lever worth examining.
- **Women in football.** The data suggests a large reserve: women hold {ui.fmt_pct(foot_share)} of football
  licences nationally, and less where the share is lowest ({', '.join(f"{r.dep_name} {ui.fmt_pct(r.share)}"
  for r in foot_low.itertuples())}).
- **{bottom['dep_name']}.** The data suggests a combined gap: the lowest licence rate in mainland France
  ({ui.fmt_rate(bottom['rate'])} against {ui.fmt_rate(france)}), with {ui.fmt_pct(qpv_bottom['pop_share'])} of its
  population in QPV and {ui.fmt_pct(qpv_bottom['lic_share'])} of its licences held by QPV residents.

These are signals from one year of licence data, not evaluations: local knowledge (facilities, school sport, informal
practice) is needed before acting.
"""
)

st.header("What the data cannot say")
st.markdown(
    f"""
- **How many people do sport.** A licence is not a person, and the census misses non-federated practice (gyms,
  running alone, informal sport, physical education at school).
- **Why.** The census has no income, facilities or travel time: the gaps shown are descriptive, not causal.
- **The QPV gap is probably understated.** QPV populations are younger: INSEE reports that
  {ui.fmt_pct(registry.QPV_UNDER_25, 0)} of QPV residents are under 25, against {ui.fmt_pct(registry.URBAN_UNDER_25, 0)}
  in the surrounding urban areas (Insee Première n° 2008, 2024). Since people under 20 hold
  {ui.fmt_pct(under_20)} of licences, a benchmark adjusted for age would probably make the QPV gap larger.
- **Participation rates by age or disability.** Our sources give no population by age, and no disabled population
  by département: seniors and disability figures are shares or lower bounds, not participation rates.
- **Trends.** 2023 only.
"""
)
ui.source_caption(ui.SOURCE_POPULATION, "INSEE QPV 2024 population; Insee Première n° 2008 (quoted).")
st.page_link("app_pages/9_Data_and_Limits.py", label="Data sources, validation and full list of limits", icon="📋")
