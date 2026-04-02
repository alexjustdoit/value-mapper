import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# Inject Streamlit secrets into os.environ before config.py reads them.
try:
    for _key, _val in st.secrets.items():
        if isinstance(_val, str):
            os.environ.setdefault(_key, _val)
except Exception:
    pass

st.set_page_config(
    page_title="Value Mapper",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

_main_pages = [
    st.Page("pages/Home.py", title="Home"),
    st.Page("pages/New_Calculator.py", title="New Calculator"),
    st.Page("pages/Scenarios.py", title="Scenarios"),
    st.Page("pages/Products.py", title="Product Library"),
]

_dev_pages = [
    st.Page("pages/Technical_Info.py", title="Technical Info"),
]

pg = st.navigation(_main_pages + _dev_pages, position="hidden")

import config  # noqa: F401 — must load after secrets injection
from app.components.sidebar import render_sidebar_header, render_sidebar_footer
from data.store import seed_demo_data

if not st.session_state.get("_seeded"):
    seed_demo_data()
    st.session_state["_seeded"] = True
    st.rerun()

render_sidebar_header()

with st.sidebar:
    for page in _main_pages:
        st.page_link(page)

pg.run()
render_sidebar_footer(_dev_pages)
