"""Hook: how many licences in France in 2023, and how unequal are they between territories?"""
import streamlit as st

from src import data, indicators, ui

fed = data.table("federations")
summary = indicators.national_summary(fed)
rates = indicators.departement_rates(data.table("lic_dep_fed"), data.table("population_dep"),
                                     indicators.territory_codes(fed))
france = indicators.national_rate(rates)
top, bottom = rates.iloc[0], rates.iloc[-1]
mainland = rates[~rates["is_overseas"]]
main_top, main_bottom = mainland.iloc[0], mainland.iloc[-1]

st.title("Sport for all?")
st.markdown("#### Territorial and social inequalities in organised sport in France, 2023")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Annual licences", ui.fmt_int(summary.licences),
          help=f"All {summary.federations} approved federations that issued licences, all places. Includes "
               f"{ui.fmt_int(summary.school_licences)} school-sport licences (UNSS, USEP).")
c2.metric("Held by women", ui.fmt_pct(summary.women_share),
          help="Women's licences ÷ (women's + men's licences). Sex is reported for every licence.")
c3.metric("Active clubs and EPA", ui.fmt_int(summary.active_structures),
          help="Clubs (non-profit associations) and EPA (approved private establishments) with at least one annual "
               "licence.")
c4.metric("Licences per 10,000 inhabitants", ui.fmt_int(france),
          help="Mainland France and overseas départements (Mayotte excluded), without school sport (UNSS, USEP) "
               "and federations reported by département only.")
ui.source_caption(ui.SOURCE_POPULATION)

st.markdown(
    f"### In **{top['dep_name']}**, there are **{ui.fmt_int(top['rate'])}** licences per 10,000 inhabitants, "
    f"**{top['rate'] / bottom['rate']:.1f} times** more than in **{bottom['dep_name']}** "
    f"({ui.fmt_int(bottom['rate'])})."
)
st.markdown(
    f"Even within mainland France the gap is {main_top['rate'] / main_bottom['rate']:.1f} to 1: "
    f"{main_top['dep_name']} ({ui.fmt_int(main_top['rate'])}) against {main_bottom['dep_name']} "
    f"({ui.fmt_int(main_bottom['rate'])}), for a national average of {ui.fmt_int(france)}."
)

st.info(
    f"**A licence is not a person.** One person can hold several licences in different federations, so "
    f"{ui.fmt_int(summary.licences)} licences does not mean {ui.fmt_int(summary.licences)} people. "
    f"The national total includes school sport (UNSS, USEP: {ui.fmt_int(summary.school_licences)} licences); "
    "territorial comparisons leave it out because those licences are recorded at the school, not at home.",
    icon="ℹ️",
)

st.markdown(
    """
**What this app looks at**
- **Territories**: where are licences per inhabitant highest and lowest, from départements down to communes?
- **Priority neighbourhoods (QPV)**, **women**, **seniors** and **disability**: who is under-represented, and where?
- **Implications & limits**: where public effort could be targeted, and what the data cannot say.
"""
)
st.page_link("pages/2_Territories.py", label="Start with the territories map", icon="🗺️")
