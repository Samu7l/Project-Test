"""Plotly figures. Each function returns a figure; titles carry the takeaway, axes carry units.

Numbers in hover text and labels are formatted in Python with ui.fmt_num / ui.fmt_rate; axis ticks and colour
bars use the same separators through the layout's `separators` setting.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src import ui

# Sequential blue ramp (light = few licences, dark = many): one hue, light -> dark.
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
COLORSCALE = [[i / (len(BLUES) - 1), c] for i, c in enumerate(BLUES)]
# Second sequential ramp (ColorBrewer YlOrBr, yellow -> brown), for women's rates beside the blue men's map.
YLORBR = ["#fff7bc", "#fee391", "#fec44f", "#fe9929", "#ec7014", "#cc4c02", "#8c2d04"]
COLORSCALE_WOMEN = [[i / (len(YLORBR) - 1), c] for i, c in enumerate(YLORBR)]
BAR = "#2a78d6"
CONTEXT = "#a8a7a1"     # gray dots: the départements that are not highlighted
NO_DATA = "#bdbcb6"     # neutral gray: communes without a rate (below the population threshold)
HIGHLIGHT = "#eb6834"   # outline of the selected département (a different hue from the blue ramp)
REFERENCE = "#7a7974"   # reference line (France average)
COLORBAR = dict(title=dict(text=f"licences per<br>{ui.fmt_num(10_000)} inh.", side="top"), thickness=12, len=0.7,
                tickformat=",")
WOMEN, MEN = "#eb6834", "#2a78d6"  # categorical slots 2 and 1 (validated pair), always in this order
# Mercator keeps France's real proportions (roughly square); the default equirectangular projection
# stretches it ~1.4× in width at this latitude.
GEOS = dict(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)", projection_type="mercator")


def _layout(fig: go.Figure, title: str, height: int) -> go.Figure:
    """Shared layout: takeaway title, tight margins, '.' decimal mark and space thousands separator.

    Small figures (height < 250, the overseas maps) get a smaller title so that it fits a narrow column.
    """
    font = dict(size=12) if height < 250 else {}
    fig.update_layout(title=dict(text=title, x=0, xanchor="left", font=font), height=height,
                      margin=dict(l=0, r=0, t=60, b=0), separators="." + ui.THOUSANDS)
    return fig


def _hover(df: pd.DataFrame, name_col: str) -> tuple[pd.DataFrame, str]:
    """customdata (pre-formatted strings) and hover template: name, rate, licences, population."""
    custom = pd.DataFrame({
        "name": df[name_col], "rate": df["rate"].map(ui.fmt_rate),
        "licences": df["licences"].map(ui.fmt_num), "population": df["population"].map(ui.fmt_num),
    })
    template = (f"<b>%{{customdata[0]}}</b><br>%{{customdata[1]}} {ui.RATE_UNIT}"
                "<br>%{customdata[2]} licences · %{customdata[3]} inhabitants<extra></extra>")
    return custom, template


def _colorbar(title: str, below: bool, suffix: str) -> dict:
    """Vertical colour bar beside a map, or horizontal under it (so it does not take width from a square map)."""
    if below:
        return dict(title=dict(text=title, side="top"), orientation="h", thickness=12, len=0.6, x=0.5,
                    xanchor="center", y=0, yanchor="top", tickformat=",", ticksuffix=suffix)
    return dict(title=dict(text=title, side="top"), thickness=12, len=0.7, tickformat=",", ticksuffix=suffix)


def departement_map(df: pd.DataFrame, geojson: dict, selected: str, title: str, z_range: tuple[float, float],
                    colorbar_title: str = ui.RATE_UNIT, tick_suffix: str = "", height: int = 620,
                    show_scale: bool = True, scale_below: bool = False,
                    colorscale: list | None = None) -> go.Figure:
    """Choropleth of départements for any indicator; the selected département is outlined.

    `df` columns: dep, value (colour), hover (pre-formatted HTML text).
    `z_range` fixes the colour scale so that the main map, the Île-de-France zoom and the overseas maps match.
    `customdata[1]` holds the département code (read back when the user clicks the map).
    """
    fig = go.Figure(go.Choropleth(
        geojson=geojson, featureidkey="properties.code", locations=df["dep"], z=df["value"],
        zmin=z_range[0], zmax=z_range[1], customdata=df[["hover", "dep"]],
        hovertemplate="%{customdata[0]}<extra></extra>", colorscale=colorscale or COLORSCALE,
        marker_line_color="white", marker_line_width=0.5, showscale=show_scale,
        colorbar=_colorbar(colorbar_title, scale_below, tick_suffix),
    ))
    sel = df[df["dep"] == selected]
    if not sel.empty:
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey="properties.code", locations=sel["dep"], z=[0] * len(sel),
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
            marker_line_color=HIGHLIGHT, marker_line_width=3, hoverinfo="skip",
        ))
    fig.update_geos(**GEOS)
    fig.update_layout(dragmode=False, clickmode="event+select")
    _layout(fig, title, height)
    if scale_below:
        fig.update_layout(margin=dict(l=0, r=0, t=70 if "<br>" in title else 40, b=70))
    return fig


def no_data_map(geojson: dict, code: str, title: str, hover: str, height: int) -> go.Figure:
    """A territory drawn in gray, for places outside the data (e.g. Mayotte)."""
    fig = go.Figure(go.Choropleth(
        geojson=geojson, featureidkey="properties.code", locations=[code], z=[0],
        colorscale=[[0, NO_DATA], [1, NO_DATA]], showscale=False, marker_line_color="white",
        marker_line_width=0.5, hovertemplate=f"{hover}<extra></extra>",
    ))
    fig.update_geos(**GEOS)
    fig.update_layout(dragmode=False)
    return _layout(fig, title, height)


def ranked_dots(df: pd.DataFrame, reference: float, highlight: list[str], title: str) -> go.Figure:
    """Every département as a dot, sorted by rate; `highlight` départements labelled, France average as a line."""
    df = df.sort_values("rate").reset_index(drop=True)
    df["position"] = df.index + 1
    custom, template = _hover(df, "dep_name")
    fig = go.Figure(go.Scatter(
        x=df["position"], y=df["rate"], mode="markers", marker=dict(size=9, color=CONTEXT),
        customdata=custom, hovertemplate=template, showlegend=False,
    ))
    hi = df[df["dep"].isin(highlight)]
    fig.add_trace(go.Scatter(
        x=hi["position"], y=hi["rate"], mode="markers+text", marker=dict(size=14, color=BAR),
        text=[f"<b>{n}</b> {ui.fmt_rate(r)}" for n, r in zip(hi["dep_name"], hi["rate"])],
        textposition=["middle right" if p < len(df) / 2 else "middle left" for p in hi["position"]],
        customdata=custom.loc[hi.index], hovertemplate=template, showlegend=False,
    ))
    fig.add_hline(y=reference, line_dash="dot", line_color=REFERENCE,
                  annotation_text=f"France average {ui.fmt_rate(reference)}", annotation_position="top left")
    fig.update_xaxes(title_text=f"{len(df)} mainland départements, from lowest to highest rate",
                     showticklabels=False, showgrid=False, zeroline=False, range=[-2, len(df) + 3])
    fig.update_yaxes(title_text=ui.RATE_UNIT, tickformat=",", rangemode="tozero")
    return _layout(fig, title, 420)


def rank_bars(df: pd.DataFrame, reference: float, x_max: float, title: str) -> go.Figure:
    """Horizontal bars of the rate for a few départements, with the France average as a reference line.

    `x_max` fixes the axis so that two bar charts shown side by side share the same scale.
    """
    df = df.iloc[::-1]  # Plotly draws the first row at the bottom
    custom, template = _hover(df, "dep_name")
    fig = go.Figure(go.Bar(
        x=df["rate"], y=df["dep_name"], orientation="h", marker_color=BAR,
        text=df["rate"].map(ui.fmt_rate), textposition="outside", cliponaxis=False,
        customdata=custom, hovertemplate=template,
    ))
    fig.add_vline(x=reference, line_dash="dot", line_color=REFERENCE,
                  annotation_text=f"France {ui.fmt_rate(reference)}", annotation_position="top")
    fig.update_xaxes(title_text=ui.RATE_UNIT, showgrid=False, range=[0, x_max * 1.12], tickformat=",")
    fig.update_yaxes(title_text=None)
    fig.update_layout(bargap=0.35)
    return _layout(fig, title, 300)


def commune_map(df: pd.DataFrame, geojson: dict, title: str) -> go.Figure:
    """Communes of one département: rate where population is above the threshold, gray otherwise."""
    rated, small = df[df["above_threshold"]], df[~df["above_threshold"]]
    fig = go.Figure()
    if not small.empty:
        custom, _ = _hover(small, "com_name")
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey="properties.code", locations=small["com"], z=[0] * len(small),
            colorscale=[[0, NO_DATA], [1, NO_DATA]], showscale=False, marker_line_color="white",
            marker_line_width=0.3, customdata=custom,
            hovertemplate=f"<b>%{{customdata[0]}}</b><br>%{{customdata[3]}} inhabitants "
                          f"(< {ui.MIN_POP_LABEL}: no rate)<br>%{{customdata[2]}} licences<extra></extra>",
        ))
    if not rated.empty:
        custom, template = _hover(rated, "com_name")
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey="properties.code", locations=rated["com"], z=rated["rate"],
            colorscale=COLORSCALE, marker_line_color="white", marker_line_width=0.3,
            customdata=custom, hovertemplate=template, colorbar=COLORBAR,
        ))
    fig.update_geos(**GEOS)
    fig.update_layout(dragmode=False)
    return _layout(fig, title, 520)


def qpv_scatter(df: pd.DataFrame, share_col: str, selected: str, title: str, y_label: str) -> go.Figure:
    """Départements: population share in QPV (x) vs a census share in QPV (y); dashed line = parity."""
    df = df[df["pop_share"] > 0]
    hover = "%{customdata[0]}<extra></extra>"
    fig = go.Figure(go.Scatter(
        x=df["pop_share"] * 100, y=df[share_col] * 100, mode="markers", marker=dict(size=9, color=CONTEXT),
        customdata=df[["hover"]], hovertemplate=hover, showlegend=False,
    ))
    sel = df[df["dep"] == selected]
    if not sel.empty:
        fig.add_trace(go.Scatter(
            x=sel["pop_share"] * 100, y=sel[share_col] * 100, mode="markers+text",
            marker=dict(size=14, color=BAR), text=[f"<b>{n}</b>" for n in sel["dep_name"]],
            textposition=["middle left" if x > df["pop_share"].max() * 50 else "middle right"
                          for x in sel["pop_share"]],
            customdata=sel[["hover"]], hovertemplate=hover, showlegend=False,
        ))
    top = max(df["pop_share"].max(), df[share_col].max()) * 100 * 1.05
    fig.add_trace(go.Scatter(x=[0, top], y=[0, top], mode="lines", line=dict(dash="dash", color=REFERENCE),
                             hoverinfo="skip", showlegend=False))
    fig.add_annotation(x=top * 0.82, y=top * 0.82, text="parity", showarrow=False, yshift=12,
                       font=dict(color=REFERENCE))
    fig.update_xaxes(title_text="share of the population living in a QPV (%)", range=[0, top], ticksuffix=" %")
    fig.update_yaxes(title_text=y_label, range=[0, top], ticksuffix=" %")
    return _layout(fig, title, 460)


def share_bars(df: pd.DataFrame, reference: float, focus: str | None, title: str, x_label: str) -> go.Figure:
    """Horizontal bars of a share (0-1) by federation, 0-100 % axis, reference line; `focus` code in orange."""
    df = df.iloc[::-1]
    colors = [HIGHLIGHT if c == focus else BAR for c in df["code"]]
    fig = go.Figure(go.Bar(
        x=df["share"] * 100, y=df["name"], orientation="h", marker_color=colors,
        text=df["share"].map(ui.fmt_pct), textposition="outside", cliponaxis=False,
        customdata=df[["hover"]], hovertemplate="%{customdata[0]}<extra></extra>",
    ))
    fig.add_vline(x=reference * 100, line_dash="dot", line_color=REFERENCE,
                  annotation_text=f"all federations {ui.fmt_pct(reference)}", annotation_position="top")
    fig.update_xaxes(title_text=x_label, range=[0, 112], ticksuffix=" %", showgrid=False)
    fig.update_yaxes(title_text=None, automargin=True)
    fig.update_layout(bargap=0.3)
    return _layout(fig, title, 120 + 26 * len(df))


def pyramid(df: pd.DataFrame, title: str, value: str = "licences", unit: str = "licences",
            decimals: int = 0) -> go.Figure:
    """Age pyramid: women to the left (negative bars), men to the right; ticks show absolute values.

    `value` is the column to plot ('licences', or 'per_100' for licences per 100 people of that age and sex).
    """
    women = df[df["sex"] == "F"].sort_values("age_order")
    men = df[df["sex"] == "H"].sort_values("age_order")
    fig = go.Figure()
    for part, sign, name, color in [(women, -1, "Women", WOMEN), (men, 1, "Men", MEN)]:
        fig.add_trace(go.Bar(
            y=part["age_band"].map(ui.age_label), x=sign * part[value], orientation="h", name=name,
            marker_color=color, customdata=part[value].map(lambda v: ui.fmt_num(v, decimals)),
            hovertemplate=f"<b>{name}, %{{y}}</b><br>%{{customdata}} {unit}<extra></extra>",
        ))
    top = df[value].max()
    ticks = _nice_ticks(top)
    tick_dec = 0 if all(float(t).is_integer() for t in ticks) else 1
    fig.update_xaxes(tickvals=[-t for t in ticks[::-1]] + ticks[1:],
                     ticktext=[ui.fmt_num(t, tick_dec) for t in ticks[::-1]] + [ui.fmt_num(t, tick_dec) for t in ticks[1:]],
                     range=[-top * 1.08, top * 1.08], title_text=f"{unit} (women ← · → men)")
    fig.update_yaxes(title_text="age band", categoryorder="array",
                     categoryarray=women["age_band"].map(ui.age_label).tolist())
    fig.update_layout(barmode="overlay", bargap=0.1, legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom"))
    _layout(fig, title, 560)
    fig.update_layout(margin=dict(l=0, r=0, t=90, b=0))
    return fig


def _nice_ticks(top: float, n: int = 3) -> list[float]:
    """0 and up to n round steps (1, 2 or 5 × 10^k) below `top`."""
    if top <= 0:
        return [0]
    raw = top / n
    mag = 10 ** int(f"{raw:e}".split("e")[1])
    step = next(m * mag for m in (1, 2, 5, 10) if m * mag >= raw)
    return [i * step for i in range(int(top // step) + 1)]


def ratio_by_age(df: pd.DataFrame, highlight: list[str], title: str) -> go.Figure:
    """Women's licence rate as a % of men's, by age band (line); 100 % = parity; `highlight` bands labelled."""
    labels = df["age_band"].map(ui.age_label)
    hover = ("<b>" + labels + "</b><br>Women's rate = " + (df["ratio"] * 100).map(lambda v: ui.fmt_num(v)) + " % of men's"
             + "<br>" + df["women_per_100"].map(lambda v: ui.fmt_num(v, 1)) + " licences per 100 women · "
             + df["men_per_100"].map(lambda v: ui.fmt_num(v, 1)) + " per 100 men")
    fig = go.Figure(go.Scatter(x=labels, y=df["ratio"] * 100, mode="lines+markers", line=dict(color=WOMEN, width=2),
                               marker=dict(size=8, color=WOMEN), customdata=hover,
                               hovertemplate="%{customdata}<extra></extra>", showlegend=False))
    hi = df[df["age_band"].isin(highlight)]
    fig.add_trace(go.Scatter(x=hi["age_band"].map(ui.age_label), y=hi["ratio"] * 100, mode="markers+text",
                             marker=dict(size=13, color=WOMEN), text=(hi["ratio"] * 100).map(lambda v: f"<b>{ui.fmt_num(v)} %</b>"),
                             textposition="top center", hoverinfo="skip", showlegend=False))
    fig.add_hline(y=100, line_dash="dot", line_color=REFERENCE, annotation_text="parity (100 %)",
                  annotation_position="top left")
    fig.update_xaxes(title_text="age band in 2023", type="category")
    fig.update_yaxes(title_text="women's licence rate as % of men's", ticksuffix=" %", rangemode="tozero",
                     range=[0, max(110, df["ratio"].max() * 115)])
    return _layout(fig, title, 380)
