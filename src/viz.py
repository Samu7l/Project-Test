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
BAR = "#2a78d6"
CONTEXT = "#a8a7a1"     # gray dots: the départements that are not highlighted
NO_DATA = "#bdbcb6"     # neutral gray: communes without a rate (below the population threshold)
HIGHLIGHT = "#eb6834"   # outline of the selected département (a different hue from the blue ramp)
REFERENCE = "#7a7974"   # reference line (France average)
COLORBAR = dict(title=dict(text=f"licences per<br>{ui.fmt_num(10_000)} inh.", side="top"), thickness=12, len=0.7,
                tickformat=",")
# Horizontal colour bar under a map, so that it does not take width from a square map.
COLORBAR_BELOW = dict(title=dict(text=ui.RATE_UNIT, side="top"), orientation="h", thickness=12, len=0.6,
                      x=0.5, xanchor="center", y=0, yanchor="top", tickformat=",")
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


def departement_map(df: pd.DataFrame, geojson: dict, selected: str, title: str, z_range: tuple[float, float],
                    height: int = 620, show_scale: bool = True, scale_below: bool = False) -> go.Figure:
    """Choropleth of départements by rate; the selected one is outlined.

    `z_range` fixes the colour scale so that the main map and the Île-de-France zoom use the same colours.
    `scale_below` puts the colour bar horizontally under the map (used for the square main map).
    `customdata[4]` holds the département code (read back when the user clicks the map).
    """
    custom, template = _hover(df, "dep_name")
    custom["dep"] = df["dep"].values
    fig = go.Figure(go.Choropleth(
        geojson=geojson, featureidkey="properties.code", locations=df["dep"], z=df["rate"],
        zmin=z_range[0], zmax=z_range[1], customdata=custom, hovertemplate=template, colorscale=COLORSCALE,
        marker_line_color="white", marker_line_width=0.5, showscale=show_scale,
        colorbar=COLORBAR_BELOW if scale_below else COLORBAR,
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
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=70))
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
