"""Disability: licences of the two disability federations (Handisport, Sport Adapté) per 10 000 inhabitants."""
import streamlit as st

from src import data, indicators, ui

fed = data.table("federations")
disability = fed[fed["is_disability"]].sort_values("code")
codes = disability["code"].tolist()
lic_dep_fed = data.table("lic_dep_fed")

rates = indicators.departement_rates(lic_dep_fed, data.table("population_dep"), codes)
france = indicators.national_rate(rates)
mainland = rates[~rates["is_overseas"]]
top, bottom = mainland.iloc[0], mainland.iloc[-1]
names = " and ".join(disability["name"])

st.title("Disability")
st.markdown(
    f"The two disability federations ({names}) issued **{ui.fmt_num(disability['lic_total'].sum())}** licences, "
    f"**{ui.fmt_rate(france)} {ui.RATE_UNIT}**. In mainland France the rate ranges from "
    f"{ui.fmt_rate(bottom['rate'])} in {bottom['dep_name']} to {ui.fmt_rate(top['rate'])} in {top['dep_name']}."
)
st.info(
    "**A lower bound.** Many disabled athletes hold a licence in an ordinary federation (football, swimming, "
    "archery…), and the census does not record disability. These figures count only the two disability "
    "federations. There is no population of disabled people by département in our sources, so this is not the "
    "share of disabled people who play sport.",
    icon="⚠️",
)

cols = st.columns(len(disability) + 1)
for col, row in zip(cols, disability.itertuples()):
    col.metric(row.name, ui.fmt_num(row.lic_total), help=f"Federation code {row.code}; all places.")
cols[-1].metric(ui.RATE_UNIT.capitalize(), ui.fmt_rate(france), help="Both federations, geocoded licences.")
ui.source_caption()

second = rates.iloc[1]  # colour scale capped here so that one outlier does not wash out the map
ui.france_maps(ui.rate_frame(rates),
               f"{top['dep_name']} stands out with {ui.fmt_rate(top['rate'])} {ui.RATE_UNIT}, "
               f"{ui.fmt_num(top['rate'] / france, 1)}× the France average",
               key="disability", colorbar_title=ui.RATE_UNIT, z_max=second["rate"],
               overseas_heading=f"Overseas (France: {ui.fmt_rate(france)})")
ui.source_caption(ui.SOURCE_POPULATION, f"{names}; licences counted at the holder's home. Colour scale capped at "
                  f"{ui.fmt_rate(second['rate'])} ({second['dep_name']}, 2nd highest): {top['dep_name']} "
                  f"({ui.fmt_rate(top['rate'])}) is shown in the darkest colour.")

dep = st.session_state["dep"]
row = rates.set_index("dep").loc[dep]
delta, fmt = ui.metric_delta(row["rate"] - france, ui.rate_decimals(row["rate"]))
m1, m2 = st.columns(2)
m1.metric(f"{row['dep_name']}: {ui.RATE_UNIT}", ui.fmt_rate(row["rate"]), delta=delta, format=fmt,
          delta_description="vs France")
m2.metric("Rank among 100 départements", f"{row['rank']} / 100")

with st.expander("Table: all départements"):
    by_fed = (lic_dep_fed[lic_dep_fed["code"].isin(codes)]
              .pivot_table(index="dep", columns="code", values="licences", aggfunc="sum", fill_value=0))
    table = rates.join(by_fed, on="dep").fillna({c: 0 for c in codes})
    labels = {"dep": "Code", "dep_name": "Département",
              **{c: n for c, n in zip(disability["code"], disability["name"])},
              "licences": "Total", "rate": f"Per {ui.fmt_num(indicators.PER)} inh."}
    ui.table(table, labels, {**{c: ui.fmt_num for c in codes}, "licences": ui.fmt_num, "rate": ui.fmt_rate})
