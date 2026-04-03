import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from app.utils import has_api_keys
from data.store import list_products, list_scenarios

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)

st.header("Value Mapper")
st.markdown(
    "Value Mapper generates **custom ROI calculators** tailored to a specific product and customer. "
    "Enter your product's value drivers, describe a prospect's situation, and get an interactive "
    "calculator with AI-estimated inputs — ready to adjust and present in any conversation."
)

# ── No API key warning ────────────────────────────────────────────────────────
if not has_api_keys():
    st.warning(
        "**No API key detected.** Add an `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` to your "
        "environment (or `.env` file) to generate calculators. "
        "See the Technical Info page for setup details.",
        icon="⚠️",
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

# ── How it works ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("How It Works")
hw1, hw2, hw3 = st.columns(3)
with hw1:
    st.markdown("**1. Configure Your Product**")
    st.caption(
        "Enter your product's name, description, and value drivers — "
        "or load a saved config from the Product Library."
    )
with hw2:
    st.markdown("**2. Describe the Customer**")
    st.caption(
        "Provide the prospect's industry, company size, and key pain points. "
        "Use a demo context to get started quickly."
    )
with hw3:
    st.markdown("**3. Build & Adjust**")
    st.caption(
        "AI generates a tailored calculator with estimated inputs. "
        "Adjust any value and ROI outputs recalculate instantly."
    )

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

st.subheader("A Portfolio of SA Tools")
st.caption(
    "Three complementary tools that cover the full pre-sales workflow — from discovery to ROI quantification. "
    "All built with AI-assisted workflows and designed for reuse."
)

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    st.markdown("**[Discovery Assistant](https://discovery-assistant.streamlit.app)**")
    st.caption("Structured discovery interviews with AI-powered insight synthesis. Builds a searchable knowledge base of customer pain points and use cases.")
with col_p2:
    st.markdown("**Value Mapper**")
    st.caption("Tailored ROI calculators generated on-the-fly. Configure once, build calculators for any customer context.")
with col_p3:
    st.markdown("**[TAM Copilot](https://tam-copilot.streamlit.app)**")
    st.caption("Market sizing assistant with multi-step TAM calculations. Generates transparent, auditable market opportunity estimates.")
