"""Women: federations ranked by women's share (national) and football's women's share by département."""
import streamlit as st

from src import data, indicators, ui, viz

FOOTBALL = "111"
MIN_LICENCES = 1_000
N_SHOWN = 15

fed = data.table("federations")
ranking = indicators.women_by_federation(fed, MIN_LICENCES)
all_share = indicators.national_summary(fed).women_share
foot = fed.set_index("code").loc[FOOTBALL]
foot_share = foot["lic_f"] / (foot["lic_f"] + foot["lic_h"])
ranking["hover"] = ("<b>" + ranking["name"] + "</b><br>" + ranking["share"].map(ui.fmt_pct) + " women<br>"
                    + ranking["lic_f"].map(ui.fmt_num) + " women · " + ranking["lic_h"].map(ui.fmt_num) + " men")

st.title("Women")
majority = (ranking["share"] > 0.5).sum()
st.markdown(
    f"Women hold **{ui.fmt_pct(all_share)}** of all licences. Among the {len(ranking)} federations with at least "
    f"{ui.fmt_num(MIN_LICENCES)} licences, **{majority}** have more women than men. In football, the largest "
    f"federation, women hold only **{ui.fmt_pct(foot_share)}** of licences."
)

c1, c2, c3 = st.columns(3)
c1.metric("Licences held by women", ui.fmt_pct(all_share), help="All federations, all places, UNSS and USEP included.")
delta, fmt = ui.metric_delta((foot_share - all_share) * 100, 1)
c2.metric("Football (FFF): women's share", ui.fmt_pct(foot_share), delta=delta, format=fmt,
          delta_description="pts vs all federations",
          help=f"{ui.fmt_num(foot['lic_f'])} women out of {ui.fmt_num(foot['lic_total'])} FFF licences "
               "(same figures as INJEP's revised 2023 results).")
c3.metric(f"Federations with a female majority (≥ {ui.fmt_num(MIN_LICENCES)} licences)",
          f"{majority} / {len(ranking)}")
ui.source_caption()

# --- Ranking ------------------------------------------------------------------------------------------------------
lowest, highest = ranking.head(N_SHOWN), ranking.tail(N_SHOWN).iloc[::-1]
st.plotly_chart(viz.share_bars(lowest, all_share, FOOTBALL,
                               f"Lowest women's share: {lowest.iloc[0]['name']} ({ui.fmt_pct(lowest.iloc[0]['share'])})",
                               "share of licences held by women (%)"), width="stretch")
st.plotly_chart(viz.share_bars(highest, all_share, FOOTBALL,
                               f"Highest women's share: {highest.iloc[0]['name']} "
                               f"({ui.fmt_pct(highest.iloc[0]['share'])})",
                               "share of licences held by women (%)"), width="stretch")
ui.source_caption(f"Federations with at least {ui.fmt_num(MIN_LICENCES)} licences, all places, school sport included. "
                  "Share = women ÷ (women + men). Football in orange when shown.")
with st.expander(f"Table: all {len(ranking)} federations"):
    ui.table(ranking.sort_values("share"),
             {"code": "Code", "name": "Federation", "group": "INJEP group", "lic_total": "Licences",
              "lic_f": "Women", "lic_h": "Men", "share": "Women's share"},
             {"lic_total": ui.fmt_num, "lic_f": ui.fmt_num, "lic_h": ui.fmt_num, "share": ui.fmt_pct})

# --- Football by département --------------------------------------------------------------------------------------
st.header("Football: women's share by département")
shares = indicators.departement_shares(data.table("lic_dep_fed"), data.table("population_dep"), [FOOTBALL],
                                       "f", "f+h")
frame = shares.assign(
    value=shares["share"] * 100, label=shares["share"].map(ui.fmt_pct),
    hover="<b>" + shares["dep_name"] + "</b><br>" + shares["share"].map(ui.fmt_pct)
          + " of football licences held by women<br>" + shares["num"].map(ui.fmt_num) + " women · "
          + shares["den"].map(ui.fmt_num) + " licences",
)
mainland = shares[~shares["is_overseas"]].sort_values("share")
lo, hi = mainland.iloc[0], mainland.iloc[-1]
ui.france_maps(frame, f"Women hold {ui.fmt_pct(lo['share'])} of football licences in {lo['dep_name']}, "
                      f"{ui.fmt_pct(hi['share'])} in {hi['dep_name']}",
               key="women", colorbar_title="share of football licences held by women", tick_suffix=" %",
               overseas_heading=f"Overseas (France: {ui.fmt_pct(foot_share)})")
ui.source_caption("FF de Football (code 111), geocoded licences at the holder's home.")

dep = st.session_state["dep"]
row = shares.set_index("dep").loc[dep]
delta, fmt = ui.metric_delta((row["share"] - foot_share) * 100, 1)
st.metric(f"Football in {row['dep_name']}: women's share", ui.fmt_pct(row["share"]), delta=delta, format=fmt,
          delta_description="pts vs France (FFF)")
