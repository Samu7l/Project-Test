"""Plotly figures. Each function returns a figure; titles carry the takeaway, axes carry units."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

RATE_UNIT = "licences per 10,000 inhabitants"
# Sequential blue ramp (light = few licences, dark = many): one hue, light -> dark.
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
COLORSCALE = [[i / (len(BLUES) - 1), c] for i, c in enumerate(BLUES)]
BAR = "#2a78d6"
NO_DATA = "#bdbcb6"     # neutral gray: communes without a rate (below the population threshold)
HIGHLIGHT = "#eb6834"   # outline of the selected département (a different hue from the blue ramp)
REFERENCE = "#7a7974"   # reference line (France average)


def _layout(fig: go.Figure, title: str, height: int) -> go.Figure:
    """Shared layout: takeaway title, tight margins."""
    fig.update_layout(title=dict(text=title, x=0, xanchor="left"), height=height,
                      margin=dict(l=0, r=0, t=60, b=0))
    return fig


def _rate_format(rates: pd.Series) -> str:
    """d3 format for rates: no decimals when values are large, one decimal for small federations."""
    return ",.0f" if rates.max() >= 100 else ",.1f"


def _map_hover(fmt: str) -> str:
    """Hover text for maps; customdata = [code, name, rate, licences, population]."""
    return (f"<b>%{{customdata[1]}}</b><br>%{{customdata[2]:{fmt}}} {RATE_UNIT}"
            "<br>%{customdata[3]:,} licences · %{customdata[4]:,} inhabitants<extra></extra>")


def departement_map(df: pd.DataFrame, geojson: dict, selected: str, title: str) -> go.Figure:
    """Choropleth of the mainland départements by rate; the selected one is outlined."""
    custom = df[["dep", "dep_name", "rate", "licences", "population"]]
    fig = go.Figure(go.Choropleth(
        geojson=geojson, featureidkey="properties.code", locations=df["dep"], z=df["rate"],
        customdata=custom, hovertemplate=_map_hover(_rate_format(df["rate"])), colorscale=COLORSCALE,
        marker_line_color="white", marker_line_width=0.5,
        colorbar=dict(title=dict(text="licences per<br>10,000 inh.", side="top"), thickness=12, len=0.7),
    ))
    sel = df[df["dep"] == selected]
    if not sel.empty:
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey="properties.code", locations=sel["dep"], z=[0] * len(sel),
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
            marker_line_color=HIGHLIGHT, marker_line_width=3, hoverinfo="skip",
        ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(dragmode=False, clickmode="event+select")
    return _layout(fig, title, 620)


def rank_bars(df: pd.DataFrame, reference: float, x_max: float, title: str) -> go.Figure:
    """Horizontal bars of the rate for a few départements, with the France average as a reference line.

    `x_max` fixes the axis so that two bar charts shown side by side share the same scale.
    """
    df = df.iloc[::-1]  # Plotly draws the first row at the bottom
    fmt = _rate_format(df["rate"].clip(lower=reference))
    fig = go.Figure(go.Bar(
        x=df["rate"], y=df["dep_name"], orientation="h", marker_color=BAR,
        texttemplate=f"%{{x:{fmt}}}", textposition="outside", cliponaxis=False,
        customdata=df[["licences", "population"]],
        hovertemplate=f"<b>%{{y}}</b><br>%{{x:{fmt}}} {RATE_UNIT}"
                      "<br>%{customdata[0]:,} licences · %{customdata[1]:,} inhabitants<extra></extra>",
    ))
    fig.add_vline(x=reference, line_dash="dot", line_color=REFERENCE,
                  annotation_text=f"France {reference:{fmt}}", annotation_position="top")
    fig.update_xaxes(title_text=RATE_UNIT, showgrid=False, range=[0, x_max * 1.12], tickformat=",")
    fig.update_yaxes(title_text=None)
    fig.update_layout(bargap=0.35)
    return _layout(fig, title, 300)


def commune_map(df: pd.DataFrame, geojson: dict, min_pop: int, title: str) -> go.Figure:
    """Communes of one département: rate where population ≥ min_pop, gray otherwise."""
    rated, small = df[df["above_threshold"]], df[~df["above_threshold"]]
    fig = go.Figure()
    if not small.empty:
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey="properties.code", locations=small["com"], z=[0] * len(small),
            colorscale=[[0, NO_DATA], [1, NO_DATA]], showscale=False, marker_line_color="white",
            marker_line_width=0.3, name=f"< {min_pop:,} inhabitants",
            customdata=small[["com_name", "population", "licences"]],
            hovertemplate=f"<b>%{{customdata[0]}}</b><br>%{{customdata[1]:,}} inhabitants (< {min_pop:,}: no rate)"
                          "<br>%{customdata[2]:,} licences<extra></extra>",
        ))
    if not rated.empty:
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey="properties.code", locations=rated["com"], z=rated["rate"],
            colorscale=COLORSCALE, marker_line_color="white", marker_line_width=0.3,
            customdata=rated[["com", "com_name", "rate", "licences", "population"]],
            hovertemplate=_map_hover(_rate_format(rated["rate"])),
            colorbar=dict(title=dict(text="licences per<br>10,000 inh.", side="top"), thickness=12, len=0.7),
        ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(dragmode=False)
    return _layout(fig, title, 520)
