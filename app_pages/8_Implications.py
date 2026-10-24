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
by_age = indicators.women_to_men_by_age(indicators.pyramid_rates(
    indicators.pyramid(data.table("pyramid"), indicators.non_school_codes(fed)), data.table("population_sex_age")))
ratio_young, ratio_adult = (by_age.set_index("age_band").loc[b, "ratio"] for b in ("10 à 14 ans", "20 à 24 ans"))
widest = by_age.loc[by_age["ratio"].idxmin()]
older = by_age[by_age["age_order"] > widest["age_order"]]
older_peak = older.loc[older["ratio"].idxmax()] if len(older) else None
higher_again = (f"; it is higher again in older age groups ({ui.fmt_num(older_peak['ratio'] * 100)} at "
                f"{ui.age_label(older_peak['age_band'])})"
                if older_peak is not None and older_peak["ratio"] > widest["ratio"] + 0.1 else "")
# Seniors
seniors = indicators.senior_rates(lic_dep_fed, pop_dep, data.table("population_sex_age"), geo_codes)
senior_rate = indicators.national_rate(seniors)
sen_main = seniors[~seniors["is_overseas"]]
# Disability
dis_codes = fed.loc[fed["is_disability"], "code"].tolist()
dis = indicators.departement_rates(lic_dep_fed, pop_dep, dis_codes)
dis_france = indicators.national_rate(dis)
# Age profile of all licences (for the QPV caveat)
pyr = indicators.pyramid(data.table("pyramid"), indicators.all_codes(fed))
known = pyr[pyr["age_band"] != "NR"]
under_20 = known.loc[known["age_order"] <= 3, "licences"].sum() / known["licences"].sum()

st.title("Implications")
st.markdown("What the 2023 census shows : Where public effort could be targeted but also what it cannot tell us ; it's only assumptions.")

st.header("Five takeaways")
st.markdown(
    f"""
1. **Territories** : In mainland France, {top['dep_name']} counts {ui.fmt_rate(top['rate'])} licences per
   {ui.fmt_num(indicators.PER)} inhabitants, **{ui.fmt_num(top['rate'] / bottom['rate'], 1)} times**
   {bottom['dep_name']} ({ui.fmt_rate(bottom['rate'])}); {overseas_below} of {len(overseas)} overseas départements are
   below the France average ({ui.fmt_rate(france)}).
2. **Priority neighbourhoods** : QPV residents are {ui.fmt_pct(nat_qpv['pop_share'])} of the population but hold
   **{ui.fmt_pct(nat_qpv['lic_share'])}** of licences; {ui.fmt_pct(nat_qpv['club_share'])} of active clubs and EPA are
   located in a QPV.
3. **Women** : Women hold {ui.fmt_pct(summary.women_share)} of all licences and only **{ui.fmt_pct(foot_share)}** in
   football, the largest federation. The gap is widest among young adults: per head, girls aged 10–14 hold
   {ui.fmt_num(ratio_young * 100)} licences per 100 held by boys, women aged 20–24 hold
   **{ui.fmt_num(ratio_adult * 100)}** per 100 held by men, and the lowest value is at
   {ui.age_label(widest['age_band'])} ({ui.fmt_num(widest['ratio'] * 100)}){higher_again} (age groups compared in
   2023, school sport excluded).
4. **Seniors** : France counts **{ui.fmt_rate(senior_rate)}** licences per {ui.fmt_num(indicators.PER)} inhabitants
   aged 60+, from {ui.fmt_rate(sen_main.iloc[-1]['rate'])} in {sen_main.iloc[-1]['dep_name']} to
   {ui.fmt_rate(sen_main.iloc[0]['rate'])} in {sen_main.iloc[0]['dep_name']} (mainland France).
5. **Disability** : The two disability federations count **{ui.fmt_rate(dis_france)}** licences per
   {ui.fmt_num(indicators.PER)} inhabitants, we can consider it as a lower bound of disabled people's sport.
"""
)

st.header("Where public effort could be targeted")
st.markdown(
    f"""
- **Priority neighbourhoods :** The data suggests that QPV residents hold about **{ui.fmt_num(nat_qpv['lic_share'] /
  nat_qpv['pop_share'], 2)}** of the licences their population share would imply, and clubs are rarer there.
  Club creation or support for existing clubs in or near QPV may be a lever worth examining.
- **Women in football :** The data suggests a large reserve: women hold {ui.fmt_pct(foot_share)} of football
  licences nationally, and less where the share is lowest ({', '.join(f"{r.dep_name} {ui.fmt_pct(r.share)}"
  for r in foot_low.itertuples())}).
- **{bottom['dep_name']} :** The data suggests a combined gap: the lowest licence rate in mainland France
  ({ui.fmt_rate(bottom['rate'])} against {ui.fmt_rate(france)}), with {ui.fmt_pct(qpv_bottom['pop_share'])} of its
  population in QPV and {ui.fmt_pct(qpv_bottom['lic_share'])} of its licences held by QPV residents.

These are signals from only one year of licence data, they are clearly not evaluations ; local knowledge such as facilities, school sport, informal
practice must be considered before acting.
"""
)

st.header("What the data cannot say")
st.markdown(
    f"""
- **How many people do sport? :** As said multiple times, a licence is not a person, and the census misses all the non-federated practice like gyms(musculation),
  running alone, informal sport, and physical education at school.
- **Why?** The census has no data on income, facilities or travel time so the gaps shown are ONLY descriptive, not causal.
- **The QPV gap is probably understated :** QPV populations are younger: INSEE reports that
  {ui.fmt_pct(registry.QPV_UNDER_25, 0)} of QPV residents are under 25, against {ui.fmt_pct(registry.URBAN_UNDER_25, 0)}
  in the surrounding urban areas (Insee Première n° 2008, 2024). So as people under 20 hold
  {ui.fmt_pct(under_20)} of licences, a benchmark adjusted for age would probably make the QPV gap larger.
- **Participation of disabled people :** As there is no disabled population by département in our sources ; disability
  figures are only lower bounds per inhabitant, not to be considered  as participation rates.
- **Trends : ** We only have data for 2023, we can improve the analysis with more recent data or more data (from 2016 to 2023 for example).
"""
)
ui.source_caption(ui.SOURCE_POPULATION, "INSEE QPV 2024 population; Insee Première n° 2008 (quoted).")
st.page_link("app_pages/9_Data_and_Limits.py", label="Data sources, validation and full list of limits", icon="📋")
