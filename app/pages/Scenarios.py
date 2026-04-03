import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uuid

import streamlit as st
from app.utils import build_export_pdf, fmt_unit
from data.models import CustomerContext, Scenario
from data.store import delete_scenario, list_scenarios, save_scenario


st.markdown("""<style>
[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}
[data-testid="stButton"] > button { white-space: nowrap; min-width: fit-content; }
</style>""", unsafe_allow_html=True)


# ── Dialogs ───────────────────────────────────────────────────────────────────

@st.dialog("Rename Calculator")
def _rename_dialog(scenario: Scenario) -> None:
    with st.form("rename_form"):
        new_name = st.text_input("Name", value=scenario.name)
        col_ok, col_cancel = st.columns(2)
        submitted = col_ok.form_submit_button("Save", type="primary", use_container_width=True)
        cancelled = col_cancel.form_submit_button("Cancel", use_container_width=True)
    if submitted and new_name.strip():
        scenario.name = new_name.strip()
        save_scenario(scenario)
    if submitted or cancelled:
        st.rerun()


@st.dialog("Edit Customer Context")
def _edit_customer_dialog(scenario: Scenario) -> None:
    c = scenario.customer
    with st.form("edit_customer_form"):
        company_name = st.text_input("Company Name *", value=c.company_name)
        col_ind, col_size = st.columns(2)
        with col_ind:
            industry = st.text_input("Industry *", value=c.industry)
        with col_size:
            company_size = st.text_input("Company Size *", value=c.company_size)
        pain_points_text = st.text_area(
            "Pain Points *  (one per line)",
            value="\n".join(c.pain_points),
            height=110,
        )
        notes = st.text_area("Additional Context", value=c.notes, height=80)
        col_save, col_cancel = st.columns(2)
        submitted = col_save.form_submit_button("Save", type="primary", use_container_width=True)
        cancelled = col_cancel.form_submit_button("Cancel", use_container_width=True)

    if submitted:
        pain_points = [l.strip() for l in pain_points_text.strip().splitlines() if l.strip()]
        if not company_name.strip() or not industry.strip() or not company_size.strip() or not pain_points:
            st.error("All required fields must be filled in.")
            return
        scenario.customer = CustomerContext(
            company_name=company_name.strip(),
            industry=industry.strip(),
            company_size=company_size.strip(),
            pain_points=pain_points,
            notes=notes.strip(),
        )
        save_scenario(scenario)
        st.session_state[f"customer_updated_{scenario.id}"] = True
        st.rerun()
    if cancelled:
        st.rerun()


@st.dialog("Regenerate Calculator")
def _regen_dialog(scenario: Scenario, calculator) -> None:
    from features.calculator_generation import generate_calculator

    adjusted = [f for f in calculator.fields if f.current_value is not None]

    st.markdown(
        "The AI will generate a new calculator for this product and customer. "
        "**All current inputs will be replaced with fresh AI estimates.**"
    )
    if adjusted:
        st.markdown(f"You have **{len(adjusted)} manually adjusted input(s)**.")

    col_fresh, col_keep, col_cancel = st.columns(3)
    fresh = col_fresh.button("Fresh start", use_container_width=True)
    keep = col_keep.button(
        "Keep adjustments",
        type="primary",
        use_container_width=True,
        disabled=not adjusted,
    )
    cancel = col_cancel.button("Cancel", use_container_width=True)

    if fresh or keep:
        with st.spinner("Regenerating…"):
            try:
                new_calc = generate_calculator(scenario.product_snapshot, scenario.customer)
                if keep and adjusted:
                    kept = {f.key: f.current_value for f in calculator.fields if f.current_value is not None}
                    for field in new_calc.fields:
                        if field.key in kept:
                            field.current_value = kept[field.key]
                # Stash old calculator before overwriting
                st.session_state[f"sc_prev_{scenario.id}"] = scenario.calculator.model_dump(mode="json")
                scenario.calculator = new_calc
                save_scenario(scenario)
                vals_key = f"sc_vals_{scenario.id}"
                if keep and adjusted:
                    st.session_state[vals_key] = {
                        f.key: (f.current_value if f.current_value is not None else f.ai_estimate)
                        for f in new_calc.fields
                    }
                else:
                    st.session_state[vals_key] = {f.key: f.ai_estimate for f in new_calc.fields}
                st.rerun()
            except Exception as e:
                st.error(f"Regeneration failed: {e}")

    if cancel:
        st.rerun()


@st.dialog("Compare With…")
def _compare_picker_dialog(current_id: str) -> None:
    candidates = [
        s for s in list_scenarios()
        if s.id != current_id and s.calculator is not None
    ]
    if not candidates:
        st.info("No other calculators available to compare with.")
        if st.button("Close", use_container_width=True):
            st.rerun()
        return
    st.caption("Select a calculator to view side by side.")
    for s in candidates:
        label = f"**{s.name}**  \n{s.customer.company_name} · {s.product_snapshot.name}"
        if st.button(label, key=f"pick_{s.id}", use_container_width=True):
            st.session_state["compare_scenario_id"] = s.id
            st.rerun()


# ── Comparison view ───────────────────────────────────────────────────────────

def _render_comparison_view(scenario_a: Scenario, scenario_b: Scenario) -> None:
    col_back, col_title = st.columns([1, 7], vertical_alignment="center")
    with col_back:
        if st.button("← Back"):
            st.session_state.pop("compare_scenario_id", None)
            st.rerun()
    with col_title:
        st.subheader("Scenario Comparison")

    st.divider()

    col_a, col_b = st.columns(2, gap="large")

    for col, scenario in ((col_a, scenario_a), (col_b, scenario_b)):
        calculator = scenario.calculator
        customer = scenario.customer
        product = scenario.product_snapshot

        with col:
            st.markdown(f"#### {scenario.name}")
            st.caption(
                f"{customer.company_name} · {customer.industry} · {customer.company_size}  \n"
                f"Product: {product.name}"
            )
            if st.button("Open →", key=f"cmp_open_{scenario.id}"):
                st.session_state["active_scenario_id"] = scenario.id
                st.session_state.pop("compare_scenario_id", None)
                st.rerun()

            st.divider()

            st.markdown("**Inputs**")
            for field in calculator.fields:
                val = field.current_value if field.current_value is not None else field.ai_estimate
                try:
                    is_int = (
                        "$" not in field.unit
                        and "%" not in field.unit
                        and float(field.ai_estimate) == int(field.ai_estimate)
                    )
                except (ValueError, TypeError):
                    is_int = False
                val_str = str(int(val)) if is_int else f"{val:,.2f}"
                indicator = "✏️" if field.current_value is not None else "🤖"
                st.markdown(f"**{field.label}**: {val_str} {fmt_unit(field.unit)} {indicator}")
                st.caption(field.description)

            st.divider()

            st.markdown("**ROI Summary**")
            for metric in calculator.output_metrics:
                value_str = metric.format_value(calculator.fields)
                with st.container(border=True):
                    st.metric(label=metric.label, value=value_str)
                    st.caption(metric.description)


# ── Calculator view ───────────────────────────────────────────────────────────

def _render_calculator_view(scenario: Scenario) -> None:
    """Render the interactive calculator for a saved scenario."""
    from data.models import Calculator

    calculator = scenario.calculator
    customer = scenario.customer
    product = scenario.product_snapshot

    # Per-scenario session state keys
    vals_key = f"sc_vals_{scenario.id}"
    prev_key = f"sc_prev_{scenario.id}"
    if vals_key not in st.session_state:
        # Seed with saved current_value or ai_estimate
        st.session_state[vals_key] = {
            f.key: (f.current_value if f.current_value is not None else f.ai_estimate)
            for f in calculator.fields
        }

    field_vals: dict = st.session_state[vals_key]

    # Capture disk-saved state before applying session overrides
    saved_vals = {
        f.key: (f.current_value if f.current_value is not None else f.ai_estimate)
        for f in calculator.fields
    }

    # Apply overrides
    for field in calculator.fields:
        if field.key in field_vals:
            field.current_value = field_vals[field.key]

    # ── Customer-updated notice ────────────────────────────────────────────────
    if st.session_state.pop(f"customer_updated_{scenario.id}", False):
        st.info("Customer context updated. Hit **Regenerate** to refresh AI estimates for the new context.")

    # ── Header ────────────────────────────────────────────────────────────────
    col_back, col_title, col_rename, col_edit_cust = st.columns([1, 5, 1, 1], vertical_alignment="center")
    with col_back:
        if st.button("← Saved Calculators"):
            st.session_state.pop("active_scenario_id", None)
            st.rerun()
    with col_title:
        st.subheader(scenario.name)
        st.caption(
            f"{customer.company_name} · {customer.industry} · {customer.company_size}  \n"
            f"Product: {product.name}"
        )
    with col_rename:
        if st.button("✏️ Rename", use_container_width=True):
            _rename_dialog(scenario)
    with col_edit_cust:
        if st.button("✏️ Customer", use_container_width=True):
            _edit_customer_dialog(scenario)

    with st.expander("Why these metrics?", expanded=False):
        st.write(calculator.rationale)

    st.divider()

    col_inputs, col_outputs = st.columns([3, 2], gap="large")

    # ── Inputs ────────────────────────────────────────────────────────────────
    with col_inputs:
        st.markdown("**Inputs**")
        st.caption("Adjust any value — outputs recalculate instantly.")

        new_vals = {}
        for field in calculator.fields:
            current = field_vals.get(field.key, field.ai_estimate)
            is_int = "$" not in field.unit and "%" not in field.unit and float(field.ai_estimate) == int(field.ai_estimate)
            col_label, col_input = st.columns([3, 2])
            with col_label:
                st.markdown(f"**{field.label}**")
                st.caption(f"{field.description}  \n*{field.value_driver}*")
            with col_input:
                val = st.number_input(
                    fmt_unit(field.unit),
                    value=int(current) if is_int else float(current),
                    min_value=0 if is_int else 0.0,
                    step=1 if is_int else max(1.0, float(current) * 0.05) if current > 0 else 1.0,
                    key=f"sc_field_{scenario.id}_{field.key}",
                    label_visibility="visible",
                )
                if val != field.ai_estimate:
                    st.caption("✏️ adjusted")
                else:
                    st.caption("🤖 AI estimate")
            new_vals[field.key] = val

    st.session_state[vals_key] = new_vals
    for field in calculator.fields:
        v = new_vals.get(field.key)
        field.current_value = v if v != field.ai_estimate else None

    # ── Outputs ───────────────────────────────────────────────────────────────
    with col_outputs:
        st.markdown("**ROI Summary**")
        for metric in calculator.output_metrics:
            value_str = metric.format_value(calculator.fields)
            with st.container(border=True):
                st.metric(label=metric.label, value=value_str)
                st.caption(metric.description)

    st.divider()

    # ── Restore banner (shown after regeneration) ─────────────────────────────
    if prev_key in st.session_state:
        col_msg, col_restore, col_dismiss = st.columns([5, 1, 1])
        col_msg.caption("↩ Previous version available")
        if col_restore.button("Restore", key="restore_prev", use_container_width=True):
            from data.models import Calculator
            old_calc = Calculator.model_validate(st.session_state[prev_key])
            scenario.calculator = old_calc
            save_scenario(scenario)
            st.session_state.pop(prev_key, None)
            st.session_state.pop(vals_key, None)
            st.rerun()
        if col_dismiss.button("Dismiss", key="dismiss_prev", use_container_width=True):
            st.session_state.pop(prev_key, None)
            st.rerun()

    # ── Save changes ──────────────────────────────────────────────────────────
    has_unsaved = any(new_vals.get(k) != saved_vals.get(k) for k in new_vals)
    if has_unsaved:
        st.caption("● Unsaved changes")

    col_save, col_regen, col_dl, col_compare = st.columns([2, 2, 2, 2])

    if col_save.button("💾  Save Changes", type="primary", use_container_width=True):
        for field in calculator.fields:
            v = new_vals.get(field.key)
            field.current_value = v if v != field.ai_estimate else None
        scenario.calculator = calculator
        save_scenario(scenario)
        st.session_state.pop(prev_key, None)
        st.success("Changes saved.")

    pdf_bytes = build_export_pdf(scenario.name, product.name, customer, calculator)
    col_dl.download_button(
        "⬇️  Export PDF",
        data=pdf_bytes,
        file_name=f"{scenario.name.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    if col_regen.button("🔄  Regenerate", use_container_width=True):
        _regen_dialog(scenario, calculator)

    if col_compare.button("⚖️  Compare", use_container_width=True):
        _compare_picker_dialog(scenario.id)


# ── Scenario list ─────────────────────────────────────────────────────────────

def _render_list() -> None:
    st.header("Saved Calculators")
    st.caption("Open any calculator to adjust inputs and review ROI outputs.")

    if st.button("+ New Calculator", type="primary"):
        st.switch_page("pages/New_Calculator.py")

    scenarios = list_scenarios()

    if not scenarios:
        st.info("No scenarios yet. Build your first calculator to get started.")
        return

    st.divider()

    for scenario in scenarios:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([5, 1, 1, 1])
            with c1:
                status = "✅ Calculator ready" if scenario.calculator else "⏳ Needs generation"
                st.markdown(f"**{scenario.name}**")
                st.caption(
                    f"{scenario.customer.company_name} · {scenario.customer.industry} · "
                    f"{scenario.product_snapshot.name}  \n{status} · "
                    f"Updated {scenario.updated_at.strftime('%b %d, %Y')}"
                )
            with c2:
                open_disabled = scenario.calculator is None
                if st.button(
                    "Open",
                    key=f"open_{scenario.id}",
                    use_container_width=True,
                    disabled=open_disabled,
                    help="Generate a calculator first" if open_disabled else None,
                ):
                    st.session_state["active_scenario_id"] = scenario.id
                    st.rerun()
            with c3:
                if st.button("Duplicate", key=f"dup_{scenario.id}", use_container_width=True):
                    dup = Scenario(
                        name=f"Copy of {scenario.name}",
                        product_snapshot=scenario.product_snapshot,
                        source_product_id=scenario.source_product_id,
                        customer=scenario.customer,
                        calculator=scenario.calculator,
                    )
                    save_scenario(dup)
                    st.rerun()
            with c4:
                if st.button("Delete", key=f"del_{scenario.id}", use_container_width=True):
                    st.session_state[f"confirm_del_{scenario.id}"] = True

            if st.session_state.get(f"confirm_del_{scenario.id}"):
                st.warning(f"Delete **{scenario.name}**?")
                c_yes, c_no = st.columns(2)
                if c_yes.button("Yes, delete", key=f"yes_{scenario.id}", use_container_width=True):
                    delete_scenario(scenario.id)
                    st.session_state.pop(f"confirm_del_{scenario.id}", None)
                    st.session_state.pop("active_scenario_id", None)
                    st.rerun()
                if c_no.button("Cancel", key=f"no_{scenario.id}", use_container_width=True):
                    st.session_state.pop(f"confirm_del_{scenario.id}", None)
                    st.rerun()


# ── Page entrypoint ───────────────────────────────────────────────────────────

# Sidebar always links here with ?view=list — use it to reset to list view
if st.query_params.get("view") == "list":
    st.session_state.pop("active_scenario_id", None)
    st.session_state.pop("compare_scenario_id", None)
    del st.query_params["view"]

active_id = st.session_state.get("active_scenario_id")
compare_id = st.session_state.get("compare_scenario_id")

if active_id and compare_id:
    all_scenarios = list_scenarios()
    sc_a = next((s for s in all_scenarios if s.id == active_id), None)
    sc_b = next((s for s in all_scenarios if s.id == compare_id), None)
    if sc_a and sc_b and sc_a.calculator and sc_b.calculator:
        _render_comparison_view(sc_a, sc_b)
    else:
        st.session_state.pop("compare_scenario_id", None)
        if sc_a and sc_a.calculator:
            _render_calculator_view(sc_a)
        else:
            st.session_state.pop("active_scenario_id", None)
            _render_list()
elif active_id:
    all_scenarios = list_scenarios()
    match = next((s for s in all_scenarios if s.id == active_id), None)
    if match and match.calculator:
        _render_calculator_view(match)
    else:
        st.session_state.pop("active_scenario_id", None)
        _render_list()
else:
    _render_list()
