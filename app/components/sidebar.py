import os
import streamlit as st
from config import SCC_MODE


_VM_BRANDING_HTML = """
<div style="min-height: 130px;">
  <div style="display:flex; justify-content:center; padding: 0.75rem 0 0.5rem 0;">
    <svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <!-- Ascending bar chart -->
      <rect x="4" y="26" width="8" height="12" rx="1.5" fill="#27AE60"/>
      <rect x="18" y="18" width="8" height="20" rx="1.5" fill="#27AE60"/>
      <rect x="32" y="9" width="8" height="29" rx="1.5" fill="#27AE60" opacity="0.75"/>
      <!-- Trend line -->
      <polyline points="8,24 22,16 36,7" stroke="#27AE60" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.45"/>
      <!-- Arrow tip -->
      <polyline points="32,5 36,7 34,11" stroke="#27AE60" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.45"/>
    </svg>
  </div>
  <p style="font-size: 1.75rem; font-weight: 700; line-height: 1.2; margin: 0 0 0.2rem 0;">Value Mapper</p>
  <p style="font-size: 0.875rem; opacity: 0.6; margin: 0; line-height: 1.4;">Build custom ROI calculators for any product</p>
</div>
"""

_SIDEBAR_CSS = """<style>
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavLink"] {
    display: none !important;
}
section[data-testid="stSidebar"] [data-testid="stLogoSpacer"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    min-height: 0 !important;
    height: auto !important;
    padding: 0 !important;
}
[data-testid="stSidebarContent"] {
    display: flex !important;
    flex-direction: column !important;
    min-height: 100vh !important;
}
[data-testid="stSidebarUserContent"] {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
    padding-top: 0.5rem !important;
}
[data-testid="stSidebarUserContent"] > div:first-child {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
}
[data-testid="stSidebarUserContent"] > div:first-child > [data-testid="stVerticalBlock"] {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
}
.element-container:has(.sidebar-footer-spacer) {
    flex: 1 !important;
    min-height: 0 !important;
}
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    position: fixed !important;
    top: 0.5rem !important;
    left: 0.5rem !important;
    z-index: 1000 !important;
    background-color: rgb(38, 39, 48) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
</style>"""

_RESET_BTN_CSS = """<style>
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    border: 1px solid #e74c3c !important;
    letter-spacing: 0.01em;
}
</style>"""


def render_sidebar_header() -> None:
    with st.sidebar:
        st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown(_VM_BRANDING_HTML, unsafe_allow_html=True)
        st.divider()


def render_sidebar_footer(dev_pages=None) -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-footer-spacer"></div>', unsafe_allow_html=True)
        st.divider()
        scc_mode = SCC_MODE

        st.subheader("LLM Provider")
        if scc_mode:
            st.toggle(
                "Use Local LLM (Ollama)",
                value=False,
                disabled=True,
                help="Local Ollama is not available on the hosted demo — the app uses OpenAI and Anthropic Claude automatically.",
            )
            st.caption("Demo uses OpenAI + Anthropic · Local Ollama available when self-hosted")
        else:
            use_local = st.toggle(
                "Use Local LLM (Ollama)",
                value=os.getenv("USE_LOCAL_LLM", "false").lower() == "true",
                help="Toggle between free local Ollama and API providers",
            )
            os.environ["USE_LOCAL_LLM"] = "true" if use_local else "false"

            if use_local:
                st.caption("Local mode · Free · requires Ollama")
            else:
                has_openai = bool(os.getenv("OPENAI_API_KEY"))
                has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
                if has_openai:
                    st.caption("✅ OpenAI key set")
                else:
                    st.warning("Set OPENAI_API_KEY in .env")
                if has_anthropic:
                    st.caption("✅ Anthropic key set")

        if dev_pages:
            with st.expander("Developers"):
                for page in dev_pages:
                    st.page_link(page)

        if scc_mode:
            st.divider()
            st.markdown(_RESET_BTN_CSS, unsafe_allow_html=True)
            if st.button("↺\u2002Reset Demo", use_container_width=True, help="Clear your session and start fresh"):
                if "token" in st.query_params:
                    del st.query_params["token"]
                st.session_state.clear()
