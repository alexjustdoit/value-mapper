import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from data.store import list_products, list_scenarios

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)

st.header("Value Mapper")
st.markdown(
    "Value Mapper generates **custom ROI calculators** tailored to a specific product and customer. "
    "Enter your product's value drivers, describe a prospect's situation, and get an interactive "
    "calculator with AI-estimated inputs — ready to adjust and present in any conversation."
)

st.divider()

# ── Quick stats ──────────────────────────────────────────────────────────────
products = list_products()
scenarios = list_scenarios()
industries = len({s.customer.industry for s in scenarios})

col1, col2, col3 = st.columns(3)
col1.metric("Products Configured", len(products))
col2.metric("Calculators Built", len(scenarios))
col3.metric("Industries Covered", industries)

st.divider()

# ── CTAs ─────────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Build a Calculator")
    st.caption("Select a product, describe a customer, and let the AI build you a tailored ROI calculator.")
    if st.button("New Calculator →", type="primary", use_container_width=True):
        st.switch_page("pages/New_Calculator.py")

with col_b:
    st.subheader("View Saved Calculators")
    st.caption("Reopen a previous calculator to adjust inputs, review ROI outputs, or present to a customer.")
    if st.button("View Calculators →", use_container_width=True):
        st.switch_page("pages/Scenarios.py")

# ── Recent scenarios ─────────────────────────────────────────────────────────
if scenarios:
    st.divider()
    st.subheader("Recent Calculators")
    for scenario in scenarios[:3]:
        status = "✅ Calculator ready" if scenario.calculator else "⏳ Needs generation"
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{scenario.name}**")
                st.caption(
                    f"{scenario.customer.company_name} · {scenario.customer.industry} · "
                    f"{scenario.product_snapshot.name} · {status}"
                )
            with c2:
                if st.button("Open", key=f"home_open_{scenario.id}", use_container_width=True):
                    st.session_state["active_scenario_id"] = scenario.id
                    st.switch_page("pages/Scenarios.py")

# ── Portfolio narrative ───────────────────────────────────────────────────────
st.divider()
st.caption(
    "Part of a portfolio of three SA/pre-sales tools: "
    "[Discovery Assistant](https://discovery-assistant.streamlit.app) · "
    "Value Mapper · "
    "[TAM Copilot](https://tam-copilot.streamlit.app)"
)
