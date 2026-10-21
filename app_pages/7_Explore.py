"""Explore: age pyramid (women left, men right) and women's / men's licence rates by département, for the federation
chosen in the sidebar."""
import streamlit as st

from src import data, indicators, ui, viz

SOURCE_CENSUS = "INSEE census 2023, population by sex and age"
COUNTS, PER_100 = "Counts", "Licences per 100 people of that age and sex"
SMALL = 20         # fewer licences than this in a département: rates are unstable (caption)
CAP_RATIO = 1.2    # top value > 1.2 × the second: colour scale capped at the second

fed = data.table("federations").set_index("code")
federation = st.session_state["federation"]
codes = indicators.all_codes(fed.reset_index()) if federation == indicators.ALL else [federation]
fed_label = ui.federation_label(federation)
pop_sex_age = data.table("population_sex_age")

pyr = indicators.pyramid_rates(indicators.pyramid(data.table("pyramid"), codes), pop_sex_age)
known = pyr[pyr["age_band"] != "NR"]
age_nr = pyr.loc[pyr["age_band"] == "NR", "licences"].sum()
total = pyr["licences"].sum()
women = pyr.loc[pyr["sex"] == "F", "licences"].sum()
under_20 = known.loc[known["age_order"] <= 3, "licences"].sum()        # bands 1–4 … 15–19
over_60 = known.loc[known["age_band"].isin(indicators.SENIOR_BANDS), "licences"].sum()

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

# --- Pyramid ------------------------------------------------------------------------------------------------------
mode = st.segmented_control("Pyramid", [COUNTS, PER_100], default=COUNTS, key="pyramid_mode") or COUNTS
sex_name = {"F": "women", "H": "men"}
pyr_label, age_nr_pyr = fed_label, age_nr
if federation == indicators.ALL:
    # One key per mode: checked by default for rates, unchecked for counts; each mode remembers its own choice.
    exclude_school = st.checkbox("Exclude school sport (UNSS, USEP)", value=(mode == PER_100),
                                 key=f"exclude_school_{'rate' if mode == PER_100 else 'counts'}")
    st.caption("School sport ends with school: its licences are almost all held by pupils, so they inflate the "
               "school-age bands in the comparison between age groups.")
    if exclude_school:
        school = fed.index[fed["is_club_address"]].tolist()
        pyr_all = indicators.pyramid_rates(
            indicators.pyramid(data.table("pyramid"), [c for c in codes if c not in school]), pop_sex_age)
        known = pyr_all[pyr_all["age_band"] != "NR"]
        age_nr_pyr = pyr_all.loc[pyr_all["age_band"] == "NR", "licences"].sum()
        pyr_label = f"{fed_label} without school sport (UNSS, USEP)"
if mode == COUNTS:
    peak = known.loc[known["licences"].idxmax()]
    fig = viz.pyramid(known, f"The largest group: {sex_name[peak['sex']]} aged {ui.age_label(peak['age_band'])} "
                             f"({ui.fmt_num(peak['licences'])} licences)")
else:
    peak = known.loc[known["per_100"].idxmax()]
    fig = viz.pyramid(known, f"Highest rate: {sex_name[peak['sex']]} aged {ui.age_label(peak['age_band'])}, "
                             f"{ui.fmt_num(peak['per_100'], 1)} licences per 100",
                      value="per_100", unit="licences per 100 people", decimals=1)
st.plotly_chart(fig, width="stretch")
ui.source_caption(
    *([SOURCE_CENSUS] if mode == PER_100 else []),
    f"{ui.first_upper(pyr_label)}, all places. Age bands as in the census (1–4, then 5-year bands, 80–99). Licences with "
    f"no age reported: {ui.fmt_num(age_nr_pyr)} (not shown)."
    + (" Per 100: licences ÷ population of that sex and age band (100 départements). It can exceed 100 because one "
       "person can hold several licences." if mode == PER_100 else ""),
)

# --- Women's and men's licence rates by département -----------------------------------------------------------------
st.header("Where do women and men play?")
if federation != indicators.ALL and fed.loc[federation, "is_club_address"]:
    st.info(f"No maps for {fed_label}: its licences are recorded at the school's address, not where pupils live, so "
            "a rate per inhabitant would compare school locations, not places of residence.", icon="ℹ️")
else:
    map_codes = indicators.territory_codes(fed.reset_index()) if federation == indicators.ALL else codes
    geojson = data.departements_geojson()
    columns = st.columns(2)
    small = []
    for col, sex, people, colorscale in [(columns[0], "F", "women", viz.COLORSCALE_WOMEN),
                                         (columns[1], "H", "men", viz.COLORSCALE)]:
        rates = indicators.sex_rates(data.table("lic_dep_fed"), data.table("population_dep"), pop_sex_age,
                                     map_codes, sex)
        mainland = rates[~rates["is_overseas"]]
        top, second, bottom = mainland.iloc[0], mainland.iloc[1], mainland.iloc[-1]
        unit = f"licences per {ui.fmt_num(indicators.PER)} {people}"
        capped = top["rate"] > CAP_RATIO * second["rate"]
        frame = mainland.assign(
            value=mainland["rate"],
            hover="<b>" + mainland["dep_name"] + "</b><br>" + mainland["rate"].map(ui.fmt_rate) + f" {unit}<br>"
                  + mainland["licences"].map(ui.fmt_num) + f" {people}'s licences · "
                  + mainland["population"].map(ui.fmt_num) + f" {people}")
        national = indicators.national_rate(rates)
        title = (f"{ui.fmt_rate(national)} per {ui.fmt_num(indicators.PER)} {people}<br>"   # two lines: half-width map
                 + ui.contrast_title(top["dep_name"], top["rate"], bottom["dep_name"], bottom["rate"], unit=unit))
        with col:
            st.plotly_chart(
                viz.departement_map(frame, geojson, "", f"{ui.first_upper(people)}: {title}",
                                    (mainland["rate"].min(), second["rate"] if capped else top["rate"]), unit,
                                    height=560, scale_below=True, colorscale=colorscale),
                width="stretch")
            if capped:
                st.caption(f"Colour scale capped at {ui.fmt_rate(second['rate'])} ({second['dep_name']}, 2nd "
                           f"highest): {top['dep_name']} ({ui.fmt_rate(top['rate'])}) is shown in the darkest colour.")
        n_small = int((mainland["licences"] < SMALL).sum())
        if n_small:
            small.append(f"{n_small} département{'s have' if n_small > 1 else ' has'} fewer than {SMALL} "
                         f"{people}'s licences")
    ui.source_caption(SOURCE_CENSUS, "Mainland France. Each map has its own colour scale: compare the geography "
                      "within each map, not the colours between maps (levels differ: the national rate is at the start of each "
                      "title). "
                      + ("Without school sport (UNSS, USEP) and federations reported by département only. "
                         if federation == indicators.ALL else ""))
    if small:
        st.caption(f"Small numbers: {'; '.join(small)}. Rates there rest on a few licences and can change a lot "
                   "with a handful of members.")
