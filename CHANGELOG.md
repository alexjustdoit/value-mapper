# Changelog

All notable changes to Value Mapper are documented here.

---

## [Unreleased]

---

## [1.0.1] — 2026-04-02

### Fixed
- **PDF export — inputs table** — removed description sub-rows; table is now a clean scannable grid. Removed Source column ("AI estimate" on every row was noise). Dollar input values no longer show unnecessary cents (95,000 not 95,000.00)
- **PDF export — output metrics** — large values (≥ 100) now round to whole numbers (3,370 hours/year, not 3,369.6). "Why These Metrics?" renamed to "Methodology & Assumptions". Blank third page eliminated by disabling auto-page-break before footer placement
- **Sidebar toggle button** — both collapsed (`»`) and expanded (`«`) states now pinned to the same fixed viewport position across all four portfolio apps (Value Mapper, TAM Copilot, Discovery Assistant, Relay)

---

## [1.0.0] — 2026-04-02

### Added
- `.env.example` — setup file referenced in README was missing; includes all supported environment variables with comments

### Changed
- Version bumped to 1.0.0 — feature set is complete and the app is production-ready on Streamlit Community Cloud

---

## [0.5.0] — 2026-04-02

### Added
- **Second demo scenario** — Orbit Analytics / SalesIQ pre-loaded on first visit (6 fields, 3 metrics: Annual Admin Time Recovered, Annual Research Time Saved, Total Annual Labour Savings ~$1.7M); makes the Compare feature immediately demoable without building a second calculator manually
- **Scenario notes** — collapsible Notes expander in every calculator view; SA can record freeform context (objections, follow-ups, adjustments rationale); collapsed when empty, auto-expanded when notes exist

### Changed
- **Technical Info** — version badge (`v0.5.0`) added at the top of the page; API key status copy corrected (no longer shows an error when only Anthropic key is set and OpenAI key is absent)

### Fixed
- `notes` field added to `Scenario` model (default `""`); existing saved scenarios load without changes

---

## [0.4.0] — 2026-04-02

### Added
- **"How it works" section** — 3-step explainer on the Home page (Configure Product → Describe Customer → Build & Adjust), positioned between the CTAs and Recent Calculators
- **No API key guard** — warning banner on Home and New Calculator when no `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or local LLM is configured; Generate Calculator button disabled until a key is present
- **Edit Customer Context** — "✏️ Customer" button in the calculator view header opens a dialog to update company name, industry, size, pain points, and notes inline; saves to disk and shows a prompt to regenerate so AI estimates stay accurate
- **Scenario comparison** — "⚖️ Compare" button in the calculator action bar opens a picker dialog; displays two calculators side by side with read-only inputs (showing current values and AI estimate / adjusted indicators) and live ROI Summary metric cards; "Open →" per side returns to the full interactive view

---

## [0.3.0] — 2026-04-02

### Added
- **PDF export** — calculators now download as a styled PDF (blue header, inputs table with AI estimate / Adjusted colour-coding, ROI Summary with prominent metric values, rationale section, footer); replaces plain-text export in both New Calculator and Saved Calculators views
- **Regenerate in New Calculator view** — Regenerate button added to the action bar after generation, matching the Fresh start / Keep adjustments dialog already available in Saved Calculators; updates both session state and the auto-saved scenario on disk

### Changed
- **Home stats** — replaced the redundant "Calculators Saved" + "Calculators Generated" pair (always identical since auto-save) with "Calculators Built" + "Industries Covered" (unique industries across saved calculators)
- **Shared utilities** — `fmt_unit()` and `build_export_pdf()` extracted to `app/utils.py`; removed duplicated `_fmt_unit` from both page files

### Fixed
- Back button in calculator view read "← Scenarios" after the rename to "Saved Calculators" — corrected to "← Saved Calculators"

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
