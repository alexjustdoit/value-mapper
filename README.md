# Value Mapper

AI-powered ROI calculator builder for Solutions Architects and pre-sales engineers.

Configure your product's value drivers once, describe a prospect's situation, and get a custom interactive calculator with AI-estimated inputs — ready to adjust and present in any sales conversation.

**[Try the live demo →](https://value-mapper.streamlit.app)**

> **Note:** Hosted on Streamlit's free tier — the app sleeps after a period of inactivity. If you see a "This app has gone to sleep" screen, click the wake-up button and allow 30–60 seconds to start.

---

## Why I built this

Static ROI calculators are product-specific — they're built once for one product and require manual rework every time the product, use case, or customer context changes. For an SA interviewing at multiple companies, or covering a diverse product portfolio, that doesn't scale.

Value Mapper solves this by separating the product configuration from the calculation itself. You define a product's value drivers in a reusable library, then enter a customer's context — and the AI builds a tailored calculator grounded in that customer's pain points and industry. Different customer, different calculator. Same product.

This is a portfolio project targeting Solutions Architect and pre-sales engineering roles. It demonstrates both domain fluency — the workflow reflects how SAs actually quantify value in deals — and technical depth: structured AI outputs, formula evaluation, provider abstraction, and a clean data model built for reuse.

Two demo products (FlowSync, SalesIQ) and two complete scenarios (Meridian Financial / FlowSync, Orbit Analytics / SalesIQ) are pre-loaded so any reviewer can explore the full workflow immediately — including the side-by-side comparison view.

---

## Workflow

**1. Product Library** — configure a product once: name, description, value drivers, and use cases. Saved configs load instantly when building a new calculator. Ad-hoc entry is also supported for one-off products.

**2. New Calculator** — a 3-step flow:
- *Step 1 — Product:* load from the library or enter details inline. Per-scenario edits never overwrite the saved product config.
- *Step 2 — Customer:* company name, industry, size, pain points, and any additional context. Five demo customer contexts are available via a picker dialog.
- *Step 3 — Generate:* the AI builds a calculator tailored to this product/customer combination — input fields with realistic industry-based estimates, output metrics with arithmetic formulas, and a rationale for why these metrics were chosen.

**3. Interactive Calculator** — the calculator is auto-saved immediately after generation so it's never lost. Adjust any AI-estimated input; all output metrics recalculate live. An unsaved changes indicator appears when session values differ from disk. Regeneration prompts for *Fresh start* or *Keep adjustments* (re-applies manual overrides to the new calculator), with a *Restore previous version* banner in case you want to roll back. Export to a styled PDF at any point.

**4. Saved Calculators** — full list of saved calculators with open, duplicate, rename, and delete actions. From any open calculator you can:
- **Edit Customer Context** — update company details inline and regenerate with the new context
- **Compare** — pick a second saved calculator and view both side by side: inputs with AI estimate / adjusted indicators, and ROI Summary metric cards for each
- **Notes** — freeform text field for SA context (objections raised, adjusted assumptions, follow-up actions)

---

## Architecture

```
LLM Router → Ollama (local, free)             ← development / zero API cost
           → GPT-5.4-nano (OpenAI API)        ← fallback when Anthropic key absent
           → Claude Sonnet 4.6 (Anthropic)    ← calculator generation (quality_required=True)
```

Calculator generation always sets `quality_required=True` — the output needs to be precise (valid Python identifier field keys, arithmetic formulas referencing only defined keys, realistic numeric estimates) and structured correctly for formula evaluation. Claude Sonnet 4.6 handles this reliably; GPT-5.4-nano is the fallback if no Anthropic key is configured.

**Formula evaluation** — output metric formulas are Python arithmetic expressions with field keys as variables (e.g. `hours_saved_per_week * 52 * avg_hourly_rate`). Evaluated with a restricted `eval()` that only exposes the field value namespace — no builtins, no globals. The AI is instructed to use only snake_case identifiers it defines, validated by the Pydantic schema before evaluation runs.

**Data model** — `ProductConfig` lives in the library and is reused across scenarios. Each `Scenario` stores a frozen snapshot of the product at generation time (`product_snapshot`) plus a `source_product_id` reference back to the library entry — so editing the saved product doesn't silently change old scenarios, but the link is preserved. JSON persistence via Pydantic's model serialization; no database.

**SCC isolation** — in Streamlit Community Cloud mode (`SCC_MODE=true`), each browser session gets a UUID token in the query params. Data is stored under `data/store/{token}/` — per-session isolation without authentication. Demo data is seeded on first load.

---

## Stack

Python · Streamlit · Pydantic v2 · OpenAI GPT-5.4-nano · Anthropic Claude Sonnet 4.6 · Ollama · fpdf2

---

## Setup

Requires Python 3.10+.

```bash
git clone https://github.com/alexjustdoit/value-mapper
cd value-mapper
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # edit: add API keys
streamlit run app/streamlit_app.py
```

Open `http://localhost:8501`. Two demo products and two complete scenarios load automatically.

**Windows:** replace `cp` with `copy` and `source venv/bin/activate` with `venv\Scripts\activate`.

**Environment variables** (in `.env`):

```bash
USE_LOCAL_LLM=true          # true → Ollama (free); false → OpenAI/Claude API
OPENAI_API_KEY=sk-...       # required when USE_LOCAL_LLM=false
ANTHROPIC_API_KEY=sk-ant-...  # optional — enables Claude Sonnet 4.6 for calculator generation
```

To run fully free locally, install [Ollama](https://ollama.com), run `ollama pull phi4`, and set `USE_LOCAL_LLM=true`. All LLM calls run on your machine at no cost. Demo session cost on API providers: ~$0.014 per calculator generated (Claude Sonnet 4.6) or ~$0.001 (GPT-5.4-nano fallback).

**Streamlit Cloud:** fork the repo, set main file to `app/streamlit_app.py`, and add keys under Settings → Secrets. Include `SCC_MODE = "true"` to enable per-session data isolation.

---

## Tests

```bash
pytest tests/ -v
```

27 tests covering Pydantic model validation, JSON serialization roundtrips, formula evaluation, calculator generation logic, and store operations.

## Project Structure

```
value-mapper/
├── app/
│   ├── streamlit_app.py        # entry point, navigation, secrets injection
│   ├── utils.py                # shared helpers: fmt_unit, build_export_pdf, has_api_keys
│   ├── components/sidebar.py   # shared sidebar header/footer
│   └── pages/                  # Home, New Calculator, Scenarios, Product Library,
│                               # Technical Info
├── features/
│   └── calculator_generation.py  # prompt construction + LLM call + schema conversion
├── llm/
│   ├── router.py               # USE_LOCAL_LLM routing + quality_required logic
│   └── providers/              # OllamaProvider, OpenAIProvider, ClaudeProvider
├── data/
│   ├── models.py               # ProductConfig, Scenario, Calculator, OutputMetric (Pydantic)
│   ├── store.py                # file-based persistence; SCC-aware base directory
│   ├── demo_products/          # FlowSync, SalesIQ — seeded on first load
│   └── demo_scenarios/         # Meridian Financial / FlowSync, Orbit Analytics / SalesIQ
└── tests/                      # pytest suite
```
