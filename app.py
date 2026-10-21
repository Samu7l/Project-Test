"""Entry point: page config, navigation and the shared sidebar.

Run with:  streamlit run app.py
"""
import streamlit as st

from src import ui

st.set_page_config(page_title="Sport for all? France 2023", page_icon="🏅", layout="wide")

# Which sidebar filters each page uses: (département, federation). Others are shown as "not applied".
PAGES = {
    st.Page("pages/1_Hook.py", title="Hook", icon="🏅", default=True): (False, False),
    st.Page("pages/2_Territories.py", title="Territories", icon="🗺️"): (True, True),
}

current = st.navigation(list(PAGES))
dep_applies, federation_applies = next(f for p, f in PAGES.items() if p.title == current.title)
ui.sidebar(dep_applies, federation_applies)
current.run()
