import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from data.store import list_products, list_scenarios

st.header("Technical Info")
st.caption("Developer reference — not shown in the main nav.")

st.subheader("LLM Routing")
use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
st.json({
    "USE_LOCAL_LLM": use_local,
    "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "phi4"),
    "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-5.4-nano"),
    "CLAUDE_MODEL": os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
    "OPENAI_KEY_SET": bool(os.getenv("OPENAI_API_KEY")),
    "ANTHROPIC_KEY_SET": bool(os.getenv("ANTHROPIC_API_KEY")),
})

st.subheader("Data Store")
products = list_products()
scenarios = list_scenarios()
st.json({
    "products": len(products),
    "scenarios": len(scenarios),
    "scenarios_with_calculator": sum(1 for s in scenarios if s.calculator),
})
