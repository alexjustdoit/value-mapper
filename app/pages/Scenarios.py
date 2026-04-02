import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from data.models import Scenario
from data.store import delete_scenario, list_scenarios, save_scenario


def _render_calculator_view(scenario: Scenario) -> None:
    """Render the interactive calculator for a saved scenario."""
    from data.models import Calculator

    calculator = scenario.calculator
    customer = scenario.customer
    product = scenario.product_snapshot

    # Per-scenario field value overrides stored in session state
    vals_key = f"sc_vals_{scenario.id}"
    if vals_key not in st.session_state:
        # Seed with saved current_value or ai_estimate
        st.session_state[vals_key] = {
            f.key: (f.current_value if f.current_value is not None else f.ai_estimate)
            for f in calculator.fields
        }

    field_vals: dict = st.session_state[vals_key]

    # Apply overrides
    for field in calculator.fields:
        if field.key in field_vals:
            field.current_value = field_vals[field.key]

    # ── Header ────────────────────────────────────────────────────────────────
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("← Scenarios"):
            st.session_state.pop("active_scenario_id", None)
            st.rerun()
    with col_title:
        st.subheader(scenario.name)
        st.caption(
            f"{customer.company_name} · {customer.industry} · {customer.company_size}  \n"
            f"Product: {product.name}"
        )

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
                    field.unit.capitalize(),
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

    # ── Save changes ──────────────────────────────────────────────────────────
    col_save, col_regen, _ = st.columns([2, 2, 3])

    if col_save.button("💾  Save Changes", type="primary", use_container_width=True):
        for field in calculator.fields:
            v = new_vals.get(field.key)
            field.current_value = v if v != field.ai_estimate else None
        scenario.calculator = calculator
        save_scenario(scenario)
        st.success("Changes saved.")

    if col_regen.button("🔄  Regenerate", use_container_width=True, help="Re-run the AI to generate a fresh calculator"):
        from features.calculator_generation import generate_calculator
        with st.spinner("Regenerating…"):
            try:
                new_calc = generate_calculator(product, customer)
                scenario.calculator = new_calc
                save_scenario(scenario)
                st.session_state.pop(vals_key, None)
                st.rerun()
            except Exception as e:
                st.error(f"Regeneration failed: {e}")


# ── Scenario list ─────────────────────────────────────────────────────────────

def _render_list() -> None:
    st.header("Scenarios")
    st.caption("Saved calculators. Open any scenario to adjust inputs and review ROI outputs.")

    if st.button("+ New Calculator", type="primary"):
        st.switch_page("pages/New_Calculator.py")

    scenarios = list_scenarios()

    if not scenarios:
        st.info("No scenarios yet. Build your first calculator to get started.")
        return

    st.divider()

    for scenario in scenarios:
        with st.container(border=True):
            c1, c2, c3 = st.columns([5, 1, 1])
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

active_id = st.session_state.get("active_scenario_id")

if active_id:
    scenarios = list_scenarios()
    match = next((s for s in scenarios if s.id == active_id), None)
    if match and match.calculator:
        _render_calculator_view(match)
    else:
        st.session_state.pop("active_scenario_id", None)
        _render_list()
else:
    _render_list()
