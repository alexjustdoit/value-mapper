import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from config import DATA_DIR, SCC_MODE
from data.store import list_products, list_scenarios

st.header("Technical Info")
st.caption("Developer reference — not shown in the main nav.")

# ── LLM Routing ──────────────────────────────────────────────────────────────

st.subheader("LLM Routing")

use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
has_openai = bool(os.getenv("OPENAI_API_KEY"))

if use_local:
    active_provider = "Ollama (local)"
    active_model = os.getenv("OLLAMA_MODEL", "phi4")
else:
    from config import CLAUDE_MODEL, OPENAI_MODEL
    if has_anthropic:
        active_provider = "Anthropic Claude (quality routing active)"
        active_model = CLAUDE_MODEL
    elif has_openai:
        active_provider = "OpenAI (no Anthropic key)"
        active_model = OPENAI_MODEL
    else:
        active_provider = "No provider configured"
        active_model = "—"

st.json({
    "active_provider": active_provider,
    "active_model": active_model,
    "USE_LOCAL_LLM": use_local,
    "OPENAI_KEY_SET": has_openai,
    "ANTHROPIC_KEY_SET": has_anthropic,
    "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "phi4"),
    "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-5.4-nano"),
    "CLAUDE_MODEL": os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
})

# ── Data Store ────────────────────────────────────────────────────────────────

st.subheader("Data Store")

products = list_products()
scenarios = list_scenarios()

scc_token = st.query_params.get("token") or st.session_state.get("_scc_token", "—")
store_path = str(DATA_DIR / scc_token) if SCC_MODE and scc_token != "—" else str(DATA_DIR)

st.json({
    "SCC_MODE": SCC_MODE,
    "scc_session_token": scc_token if SCC_MODE else "N/A",
    "store_path": store_path,
    "products": len(products),
    "scenarios": len(scenarios),
    "scenarios_with_calculator": sum(1 for s in scenarios if s.calculator),
})

# ── Stack Versions ────────────────────────────────────────────────────────────

st.subheader("Stack Versions")

import importlib.metadata

def _version(pkg: str) -> str:
    try:
        return importlib.metadata.version(pkg)
    except Exception:
        return "unknown"

st.json({
    "python": sys.version.split()[0],
    "streamlit": _version("streamlit"),
    "pydantic": _version("pydantic"),
    "openai": _version("openai"),
    "anthropic": _version("anthropic"),
    "httpx": _version("httpx"),
})
