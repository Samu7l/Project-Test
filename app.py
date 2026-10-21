"""Entry point: page config, navigation and the shared sidebar.

Run with:  streamlit run app.py
"""
import streamlit as st

from src import ui

st.set_page_config(page_title="Sport for all? France 2023", page_icon="🏅", layout="wide")

# Which sidebar filters each page uses: (département, federation, federation list). Unused filters are shown
# disabled as "not applied". GEO_SCOPE: federations of territorial views; NATIONAL_SCOPE: every federation.
PAGES = {
    st.Page("app_pages/1_Hook.py", title="Hook", icon="🏅", default=True): (False, False, ui.GEO_SCOPE),
    st.Page("app_pages/2_Territories.py", title="Territories", icon="🗺️"): (True, True, ui.GEO_SCOPE),
    st.Page("app_pages/3_QPV.py", title="Priority neighbourhoods", icon="🏘️"): (True, True, ui.GEO_SCOPE),
    st.Page("app_pages/4_Women.py", title="Women", icon="♀️"): (True, False, ui.GEO_SCOPE),
    st.Page("app_pages/5_Seniors.py", title="Seniors", icon="🧓"): (True, True, ui.GEO_SCOPE),
    st.Page("app_pages/6_Disability.py", title="Disability", icon="♿"): (True, False, ui.GEO_SCOPE),
    st.Page("app_pages/7_Explore.py", title="Explore", icon="🔎"): (False, True, ui.NATIONAL_SCOPE),
    st.Page("app_pages/8_Implications.py", title="Implications", icon="💡"): (False, False, ui.GEO_SCOPE),
    st.Page("app_pages/9_Data_and_Limits.py", title="Data & Limits", icon="📋"): (False, False, ui.GEO_SCOPE),
}

current = st.navigation(list(PAGES))
ui.sidebar(*next(f for p, f in PAGES.items() if p.title == current.title))
current.run()
