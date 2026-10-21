"""Seniors: share of licences held by people aged 60+, by département."""
import streamlit as st

from src import data, indicators, ui

fed = data.table("federations")
federation = st.session_state["federation"]
codes = indicators.selected_codes(fed, federation)
fed_label = ui.federation_label(federation)

shares = indicators.departement_shares(data.table("lic_dep_fed"), data.table("population_dep"), codes,
                                       "age_60p", "age_known")
france = shares["num"].sum() / shares["den"].sum()
mainland = shares[~shares["is_overseas"]].dropna(subset=["share"]).sort_values("share")
lo, hi = mainland.iloc[0], mainland.iloc[-1]

st.title("Seniors")
st.markdown(
    f"People aged 60 and over hold **{ui.fmt_pct(france)}** of the licences of {fed_label}. In mainland France the "
    f"share ranges from {ui.fmt_pct(lo['share'])} in {lo['dep_name']} to {ui.fmt_pct(hi['share'])} in "
    f"{hi['dep_name']}."
)
st.info(
    "**Read with care: this share partly reflects each département's age structure.** A département with many "
    "older residents will show a higher share of senior licences even if seniors there do not play more sport. "
    "The census gives licences by age, but our sources give no population by age, so this is not a participation "
    "rate.",
    icon="⚠️",
)

frame = shares.assign(
    value=shares["share"] * 100, label=shares["share"].map(ui.fmt_pct),
    hover="<b>" + shares["dep_name"] + "</b><br>" + shares["share"].map(ui.fmt_pct)
          + " of licences held by people aged 60+<br>" + shares["num"].map(ui.fmt_num) + " of "
          + shares["den"].map(ui.fmt_num) + " licences with a known age",
)
ui.france_maps(frame, f"{hi['dep_name']} has the highest share of 60+ licences ({ui.fmt_pct(hi['share'])}), "
                      f"{lo['dep_name']} the lowest ({ui.fmt_pct(lo['share'])})",
               key="seniors", colorbar_title="share of licences held by people aged 60+", tick_suffix=" %",
               overseas_heading=f"Overseas (France: {ui.fmt_pct(france)})")
ui.source_caption(f"{fed_label.capitalize()}, without school sport (UNSS, USEP) and federations reported by "
                  "département only. Age bands 60-64 to 80-99; licences with no age reported are left out.")

dep = st.session_state["dep"]
row = shares.set_index("dep").loc[dep]
m1, m2 = st.columns(2)
if row["den"] > 0:
    delta, fmt = ui.metric_delta((row["share"] - france) * 100, 1)
    m1.metric(f"{row['dep_name']}: licences held by people aged 60+", ui.fmt_pct(row["share"]), delta=delta,
              format=fmt, delta_description="pts vs France")
    m2.metric("Rank among 100 départements", f"{int(row['rank'])} / 100")
else:
    m1.metric(f"{row['dep_name']}: licences held by people aged 60+", "—", help="No licence for this federation.")

with st.expander("Table: all départements"):
    ui.table(shares.sort_values("share", ascending=False),
             {"dep": "Code", "dep_name": "Département", "num": "Licences 60+", "den": "Licences (known age)",
              "share": "Share 60+"},
             {"num": ui.fmt_num, "den": ui.fmt_num, "share": ui.fmt_pct})
