"""Entry point: page config, navigation and the shared sidebar.

Run with:  streamlit run app.py
"""
import streamlit as st

from src import ui

st.set_page_config(page_title="Sport for all? France 2023", page_icon="🏅", layout="wide")

pages = st.navigation([
    st.Page("pages/1_Hook.py", title="Hook", icon="🏅", default=True),
    st.Page("pages/2_Territories.py", title="Territories", icon="🗺️"),
])
ui.sidebar()
pages.run()
