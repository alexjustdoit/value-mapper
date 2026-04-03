import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pydantic
import streamlit as st

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)

import config  # noqa: F401
from config import SCC_MODE
from data.store import list_products, list_scenarios
from llm.router import LLMRouter

st.title("Technical Info")
st.caption("Developer reference — provider config, routing rules, environment, and data stats.")

router = LLMRouter()
use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
has_openai = bool(os.getenv("OPENAI_API_KEY"))

# ── Provider Architecture ──────────────────────────────────────────────────────

st.subheader("LLM Provider Architecture")

import pandas as pd

provider_data = {
    "Provider": ["Ollama (local)", "GPT-5.4-nano", "Claude Sonnet 4.6"],
    "Cost": ["Free", "~$0.001/call", "~$0.014/call"],
    "Use Case": ["Development / zero-cost demo", "Fallback when no Anthropic key", "Calculator generation (quality_required=True)"],
}
st.dataframe(pd.DataFrame(provider_data), use_container_width=True, hide_index=True)

st.divider()

# ── Active Provider Config ─────────────────────────────────────────────────────

st.subheader("Active Provider Config")

col1, col2 = st.columns(2)
with col1:
    mode = "Local (Ollama)" if use_local else "API"
    st.metric("Mode", mode)
with col2:
    if use_local:
        st.metric("Calculator Generation", router.DEFAULT_LOCAL_MODEL)
    elif has_anthropic:
        st.metric("Calculator Generation", router.DEFAULT_QUALITY_API)
    else:
        st.metric("Calculator Generation", f"{router.DEFAULT_CHEAP_API} (fallback — no Anthropic key)")

st.subheader("API Keys")
col1, col2 = st.columns(2)
with col1:
    if has_anthropic:
        st.success("✅ ANTHROPIC_API_KEY set")
    else:
        st.warning("⚠️ ANTHROPIC_API_KEY not set — falling back to GPT-5.4-nano")
with col2:
    if has_openai:
        st.success("✅ OPENAI_API_KEY set")
    else:
        st.error("❌ OPENAI_API_KEY not set — generation will fail")

st.divider()

# ── Quality Routing Rules ──────────────────────────────────────────────────────

st.subheader("Quality Routing Rules")
st.caption(
    "When USE_LOCAL_LLM=false, features flagged quality_required=True route to Claude Sonnet 4.6 "
    "if ANTHROPIC_API_KEY is set, otherwise fall back to GPT-5.4-nano."
)

routing_rows = [
    {
        "Feature": "Calculator Generation",
        "quality_required": "True",
        "Reason": "Structured output requires valid Python identifiers, correct formulas, and realistic estimates",
    },
]
st.dataframe(pd.DataFrame(routing_rows), use_container_width=True, hide_index=True)

st.divider()

# ── Environment Variables ──────────────────────────────────────────────────────

st.subheader("Environment Variables")


def _mask(val: str | None) -> str:
    if not val:
        return "—"
    if len(val) <= 8:
        return "***"
    return val[:4] + "***" + val[-4:]


env_rows = [
    {
        "Variable": "USE_LOCAL_LLM",
        "Current Value": os.getenv("USE_LOCAL_LLM", "false"),
        "Default": "false",
        "Description": "true → Ollama (free); false → OpenAI + Claude",
    },
    {
        "Variable": "OPENAI_API_KEY",
        "Current Value": _mask(os.getenv("OPENAI_API_KEY")),
        "Default": "—",
        "Description": "Required when USE_LOCAL_LLM=false and no Anthropic key",
    },
    {
        "Variable": "ANTHROPIC_API_KEY",
        "Current Value": _mask(os.getenv("ANTHROPIC_API_KEY")),
        "Default": "—",
        "Description": "Enables Claude Sonnet 4.6 for calculator generation",
    },
    {
        "Variable": "OPENAI_MODEL",
        "Current Value": os.getenv("OPENAI_MODEL", "gpt-5.4-nano"),
        "Default": "gpt-5.4-nano",
        "Description": "Override the default OpenAI model",
    },
    {
        "Variable": "CLAUDE_MODEL",
        "Current Value": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
        "Default": "claude-sonnet-4-6",
        "Description": "Override the default Claude model",
    },
    {
        "Variable": "OLLAMA_BASE_URL",
        "Current Value": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "Default": "http://localhost:11434",
        "Description": "Ollama API endpoint (override for WSL2 / remote host)",
    },
    {
        "Variable": "SCC_MODE",
        "Current Value": os.getenv("SCC_MODE", "false"),
        "Default": "false",
        "Description": "true → per-session data isolation for Streamlit Cloud hosting",
    },
]
st.dataframe(pd.DataFrame(env_rows), use_container_width=True, hide_index=True)

st.divider()

# ── Data Store ─────────────────────────────────────────────────────────────────

st.subheader("Data Store")

scc_token = st.query_params.get("token") or st.session_state.get("_scc_token", "—")

try:
    from config import DATA_DIR
    store_path = str(DATA_DIR / scc_token) if SCC_MODE and scc_token != "—" else str(DATA_DIR)
except Exception:
    store_path = "—"

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("SCC Mode", "On" if SCC_MODE else "Off")
with col2:
    products = list_products()
    scenarios = list_scenarios()
    st.metric("Products", len(products))
with col3:
    st.metric("Scenarios", len(scenarios))

if SCC_MODE:
    st.caption(f"Session token: `{scc_token}`")
st.caption(f"Store path: `{store_path}`")

st.divider()

# ── Stack ──────────────────────────────────────────────────────────────────────

st.subheader("Stack")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
with col2:
    st.metric("Streamlit", st.__version__)
with col3:
    st.metric("Pydantic", pydantic.__version__)

st.divider()

# ── Links ──────────────────────────────────────────────────────────────────────

st.subheader("Links")
st.markdown("""
- [GitHub Repository](https://github.com/alexjustdoit/value-mapper)
- [Streamlit Docs — st.navigation](https://docs.streamlit.io/develop/api-reference/navigation/st.navigation)
- [Ollama Model Library](https://ollama.com/library)
""")
