"""Hook: how many licences in France in 2023, and how unequal are they between territories?"""
import streamlit as st

from src import data, indicators, ui, viz

fed = data.table("federations")
summary = indicators.national_summary(fed)
rates = indicators.departement_rates(data.table("lic_dep_fed"), data.table("population_dep"),
                                     indicators.territory_codes(fed))
france = indicators.national_rate(rates)
mainland = rates[~rates["is_overseas"]]
main_top, main_bottom = mainland.iloc[0], mainland.iloc[-1]
lowest = rates.iloc[-1]

st.title("Sport for all?")
st.markdown("#### Territorial and social inequalities in organised sport in France, 2023")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Annual licences", ui.fmt_num(summary.licences),
          help=f"All {summary.federations} approved federations that issued licences, all places. Includes "
               f"{ui.fmt_num(summary.school_licences)} school-sport licences (UNSS, USEP).")
c2.metric("Held by women", ui.fmt_pct(summary.women_share),
          help="Women's licences ÷ (women's + men's licences). Sex is reported for every licence.")
c3.metric("Active clubs and EPA", ui.fmt_num(summary.active_structures),
          help="Clubs (non-profit associations) and EPA (approved private establishments) with at least one annual "
               "licence.")
c4.metric(f"Licences per {ui.fmt_num(indicators.PER)} inhabitants", ui.fmt_rate(france),
          help="Mainland France and overseas départements (Mayotte excluded), without school sport (UNSS, USEP) "
               "and federations reported by département only.")
ui.source_caption(ui.SOURCE_POPULATION)

st.markdown(
    f"### In mainland France, **{main_top['dep_name']}** counts **{ui.fmt_rate(main_top['rate'])}** licences per "
    f"{ui.fmt_num(indicators.PER)} inhabitants: **{main_top['rate'] / main_bottom['rate']:.1f} to 1** against "
    f"**{main_bottom['dep_name']}** ({ui.fmt_rate(main_bottom['rate'])})."
)
if lowest["is_overseas"]:
    st.markdown(
        f"Overseas, the gap is wider still: {lowest['dep_name']} has the lowest rate of all "
        f"({ui.fmt_rate(lowest['rate'])}), {main_top['rate'] / lowest['rate']:.1f} to 1 against "
        f"{main_top['dep_name']}. The national average is {ui.fmt_rate(france)}."
    )

st.plotly_chart(
    viz.ranked_dots(mainland, france, [main_top["dep"], main_bottom["dep"]],
                    f"{(mainland['rate'] < france).sum()} of {len(mainland)} mainland départements are below the "
                    f"France average; {main_bottom['dep_name']} is last"),
    width="stretch",
)
ui.source_caption(ui.SOURCE_POPULATION, "Without school sport (UNSS, USEP) and federations reported by département "
                  "only. The France average includes the overseas départements.")

st.info(
    f"**A licence is not a person.** One person can hold several licences in different federations, so "
    f"{ui.fmt_num(summary.licences)} licences does not mean {ui.fmt_num(summary.licences)} people. "
    f"The national total includes school sport (UNSS, USEP: {ui.fmt_num(summary.school_licences)} licences); "
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
