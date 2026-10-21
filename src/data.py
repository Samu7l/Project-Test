"""Cached loaders: the app reads the processed files only (built by `python -m src.build`)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"


@st.cache_data
def table(name: str) -> pd.DataFrame:
    """One processed parquet table, e.g. table('lic_dep_fed')."""
    return pd.read_parquet(PROCESSED / f"{name}.parquet")


@st.cache_data
def departements_geojson() -> dict:
    """Mainland département outlines (96 features, property `code`)."""
    return json.loads((PROCESSED / "geo" / "departements_metro.geojson").read_text())


@st.cache_data
def communes_geojson(dep: str) -> dict:
    """Simplified commune outlines of one département (property `code`)."""
    return json.loads((PROCESSED / "geo" / "communes" / f"{dep}.geojson").read_text())
