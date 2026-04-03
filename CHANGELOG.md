# Changelog

All notable changes to Value Mapper are documented here.

---

## [Unreleased]

---

## [0.2.0] — 2026-04-02

### Added
- **Auto-save on generation** — calculator is saved to disk immediately after AI generation; no work is ever lost
- **Rename & Save flow** — after generation, a dialog prompts to optionally rename before overwriting the auto-save
- **Inline rename** — ✏️ Rename button in the calculator view header opens a dialog; Enter key submits
- **Duplicate calculator** — one-click duplicate from the Saved Calculators list
- **Export / download** — download any calculator as a plain-text file from both the New Calculator and Saved Calculators views
- **Unsaved changes indicator** — `● Unsaved changes` appears above the action bar when session values differ from what's on disk
- **Regeneration confirmation dialog** — Regenerate now prompts with two options: *Fresh start* (all new AI estimates) or *Keep adjustments* (re-applies manually overridden values to the new calculator)
- **Restore previous version** — a temporary banner appears after regeneration offering one-click rollback to the prior calculator
- **Portfolio narrative footer** — Home page links to all three portfolio apps (Discovery Assistant, Value Mapper, TAM Copilot)
- **API key status indicators** on Technical Info page (✅/⚠️/❌ per key)
- **GitHub Actions keepalive** — pings the app every 6 hours to prevent Streamlit Community Cloud sleep

### Changed
- **Upgraded LLM**: calculator generation now uses Claude Sonnet 4.6 (was Haiku 4.5) for better formula consistency and more realistic estimates; ~$0.014/call vs ~$0.001 GPT-5.4-nano fallback
- **Renamed "Scenarios" → "Saved Calculators"** throughout the UI (page title, sidebar nav, Home metrics, section headers)
- **Sidebar "Saved Calculators" link** always returns to the list view, even when a calculator is open
- **Currency unit display** — `$`/`usd`/`USD` normalised to `$ USD`; GBP and EUR handled too; AI prompt locked to `$` for USD
- **Prompt instruction** added to always use `$` for monetary units
- Demo customer picker on Step 2 replaced with a dialog (was a selectbox, then a random-fill button)
- Back button in calculator view vertically centred with title
- Technical Info page updated: Sonnet 4.6 references, corrected cost figures, provider architecture table

### Fixed
- `Fresh start` regeneration was retaining adjusted values — fixed by explicitly setting session state to new AI estimates instead of popping and relying on re-seeding
- Cold-start sidebar flash — nav-hiding CSS injected at the earliest render point in every page file
- `USE_LOCAL_LLM` env var defaulted to `true` in router, inconsistent with `config.py` — corrected to `false`
- Button text wrapping at narrow viewport widths (`white-space: nowrap` + `min-width: fit-content`)
- Product dialog centering and width
- `ProductConfig()` `ValidationError` on new product entry — replaced with explicit `uuid.uuid4()`

---

## [0.1.0] — 2026-04-01

### Added
- Initial build
- **Product Library** — create, edit, and reuse product configs (name, description, value drivers, use cases)
- **New Calculator** — 3-step flow: Product → Customer → Generate
- **AI calculator generation** — structured output via Claude/OpenAI: 4–8 input fields with AI estimates, 2–5 output metrics with Python arithmetic formulas, rationale
- **Interactive calculator view** — live-recalculating outputs as inputs are adjusted; ✏️ adjusted / 🤖 AI estimate indicators per field
- **Save scenario** — named calculators persisted as JSON
- **Saved Calculators list** — open, delete, regenerate saved calculators
- **LLM provider abstraction** — Ollama (local/free), OpenAI, Anthropic; routed by `USE_LOCAL_LLM` and `quality_required` flag
- **SCC isolation** — per-session UUID token for Streamlit Community Cloud multi-user safety
- **Demo seeding** — FlowSync and SalesIQ products + Meridian Financial scenario pre-loaded on first run
- **Technical Info** page — provider config, routing rules, env vars, data store stats, stack versions
- Formula evaluation via restricted `eval()` — only field key namespace exposed, no builtins
- `Scenario.product_snapshot` — frozen copy at generation time; `source_product_id` preserves library reference
