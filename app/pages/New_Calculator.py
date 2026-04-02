import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from data.models import CustomerContext, ProductConfig, Scenario, ValueDriver
from data.store import list_products, save_product, save_scenario
from features.calculator_generation import generate_calculator

# Session state keys
_STEP = "nc_step"           # 1 | 2 | 3 | "calculator"
_PRODUCT = "nc_product"     # ProductConfig dict
_CUSTOMER = "nc_customer"   # CustomerContext dict
_CALCULATOR = "nc_calc"     # Calculator dict
_FIELD_VALS = "nc_field_vals"  # {field_key: float} — SA-adjusted values


def _reset():
    for key in [_STEP, _PRODUCT, _CUSTOMER, _CALCULATOR, _FIELD_VALS]:
        st.session_state.pop(key, None)


def _step() -> int | str:
    return st.session_state.get(_STEP, 1)


def _render_progress(current: int | str) -> None:
    steps = ["1. Product", "2. Customer", "3. Generate & Review"]
    step_num = {"calculator": 3}.get(current, current)
    cols = st.columns(len(steps))
    for i, (col, label) in enumerate(zip(cols, steps), start=1):
        if i < step_num:
            col.markdown(f"~~{label}~~ ✓")
        elif i == step_num:
            col.markdown(f"**{label}**")
        else:
            col.markdown(f"<span style='opacity:0.4'>{label}</span>", unsafe_allow_html=True)


def _parse_value_drivers(text: str) -> list[ValueDriver]:
    drivers = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            parts = line.split("|", 1)
            drivers.append(ValueDriver(name=parts[0].strip(), description=parts[1].strip()))
        else:
            drivers.append(ValueDriver(name=line, description=""))
    return drivers


def _parse_list(text: str) -> list[str]:
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


def _drivers_to_text(drivers: list[ValueDriver]) -> str:
    return "\n".join(
        f"{d.name} | {d.description}" if d.description else d.name
        for d in drivers
    )


# ── Step 1: Product config ───────────────────────────────────────────────────

def _render_step1() -> None:
    st.subheader("Step 1 — Product Configuration")
    st.caption(
        "Load a saved product or enter details below. "
        "Any edits here apply only to this scenario — your saved configs are unchanged."
    )

    products = list_products()
    saved_product: ProductConfig | None = None

    if products:
        options = ["— Enter manually —"] + [p.name for p in products]
        choice = st.selectbox("Load from Product Library", options)
        if choice != "— Enter manually —":
            saved_product = next(p for p in products if p.name == choice)

    prefill = saved_product
    preloaded = st.session_state.get(_PRODUCT)
    if preloaded and not saved_product:
        # Came back to step 1 from step 2 — restore previous entries
        prefill = ProductConfig.model_validate(preloaded)

    with st.form("nc_product_form"):
        name = st.text_input(
            "Product Name *",
            value=prefill.name if prefill else "",
        )
        description = st.text_area(
            "What does it do? *",
            value=prefill.description if prefill else "",
            height=200,
        )
        drivers_text = st.text_area(
            "Value Drivers *  (one per line: Name | Description)",
            value=_drivers_to_text(prefill.value_drivers) if prefill else "",
            placeholder="Time Savings | Eliminates manual data entry across workflows\nCost Reduction | Reduces headcount for repetitive tasks",
            height=240,
        )
        use_cases_text = st.text_area(
            "Use Cases  (optional, one per line)",
            value="\n".join(prefill.use_cases) if prefill else "",
            height=200,
        )

        save_to_library = st.checkbox(
            "Save this product to my library",
            value=False,
            help="Saves the product config for reuse in future calculators.",
        )

        col_next, col_cancel = st.columns([3, 1])
        with col_next:
            next_btn = st.form_submit_button("Next: Customer Context →", type="primary", use_container_width=True)
        with col_cancel:
            cancel_btn = st.form_submit_button("Cancel", use_container_width=True)

    if cancel_btn:
        _reset()
        st.switch_page("pages/Home.py")

    if next_btn:
        if not name.strip():
            st.error("Product name is required.")
            return
        if not description.strip():
            st.error("Description is required.")
            return
        drivers = _parse_value_drivers(drivers_text)
        if not drivers:
            st.error("At least one value driver is required.")
            return

        product = ProductConfig(
            id=saved_product.id if saved_product else ProductConfig().id,
            name=name.strip(),
            description=description.strip(),
            value_drivers=drivers,
            use_cases=_parse_list(use_cases_text),
        )

        if save_to_library:
            save_product(product)

        st.session_state[_PRODUCT] = product.model_dump(mode="json")
        st.session_state[_STEP] = 2
        st.rerun()


# ── Step 2: Customer context ─────────────────────────────────────────────────

def _render_step2() -> None:
    st.subheader("Step 2 — Customer Context")
    st.caption("Describe the prospect or customer this calculator is being built for.")

    preloaded = st.session_state.get(_CUSTOMER)
    prefill = CustomerContext.model_validate(preloaded) if preloaded else None

    with st.form("nc_customer_form"):
        company_name = st.text_input(
            "Company Name *",
            value=prefill.company_name if prefill else "",
            placeholder="e.g. Meridian Financial",
        )
        col_ind, col_size = st.columns(2)
        with col_ind:
            industry = st.text_input(
                "Industry *",
                value=prefill.industry if prefill else "",
                placeholder="e.g. Financial Services, Healthcare, B2B SaaS",
            )
        with col_size:
            company_size = st.text_input(
                "Company Size *",
                value=prefill.company_size if prefill else "",
                placeholder="e.g. 200–500 employees",
            )
        pain_points_text = st.text_area(
            "Pain Points *  (one per line)",
            value="\n".join(prefill.pain_points) if prefill else "",
            placeholder="Manual reconciliation takes 3 analysts 60% of their time\nHigh error rate in data entry causing downstream rework",
            height=110,
        )
        notes = st.text_area(
            "Additional Context  (optional)",
            value=prefill.notes if prefill else "",
            placeholder="Any other context that might affect the ROI calculation — budget constraints, timeline, current tooling, etc.",
            height=80,
        )

        col_back, col_gen = st.columns([1, 3])
        with col_back:
            back_btn = st.form_submit_button("← Back", use_container_width=True)
        with col_gen:
            gen_btn = st.form_submit_button("Generate Calculator →", type="primary", use_container_width=True)

    if back_btn:
        st.session_state[_STEP] = 1
        st.rerun()

    if gen_btn:
        if not company_name.strip():
            st.error("Company name is required.")
            return
        if not industry.strip() or not company_size.strip():
            st.error("Industry and company size are required.")
            return
        pain_points = _parse_list(pain_points_text)
        if not pain_points:
            st.error("At least one pain point is required.")
            return

        customer = CustomerContext(
            company_name=company_name.strip(),
            industry=industry.strip(),
            company_size=company_size.strip(),
            pain_points=pain_points,
            notes=notes.strip(),
        )
        st.session_state[_CUSTOMER] = customer.model_dump(mode="json")
        st.session_state[_STEP] = 3
        st.rerun()


# ── Step 3: Generate ─────────────────────────────────────────────────────────

def _render_step3() -> None:
    st.subheader("Step 3 — Generating Your Calculator")

    product = ProductConfig.model_validate(st.session_state[_PRODUCT])
    customer = CustomerContext.model_validate(st.session_state[_CUSTOMER])

    if _CALCULATOR not in st.session_state:
        with st.spinner(f"Building a custom ROI calculator for {customer.company_name}…"):
            try:
                calculator = generate_calculator(product, customer)
                st.session_state[_CALCULATOR] = calculator.model_dump(mode="json")
                st.session_state[_FIELD_VALS] = {}
                st.session_state[_STEP] = "calculator"
                st.rerun()
            except Exception as e:
                st.error(f"Generation failed: {e}")
                if st.button("← Back to Customer Context"):
                    st.session_state[_STEP] = 2
                    st.rerun()
    else:
        st.session_state[_STEP] = "calculator"
        st.rerun()


# ── Calculator view ───────────────────────────────────────────────────────────

def _render_calculator() -> None:
    from data.models import Calculator

    product = ProductConfig.model_validate(st.session_state[_PRODUCT])
    customer = CustomerContext.model_validate(st.session_state[_CUSTOMER])
    calculator = Calculator.model_validate(st.session_state[_CALCULATOR])
    field_vals: dict = st.session_state.get(_FIELD_VALS, {})

    # Apply saved SA overrides to calculator fields
    for field in calculator.fields:
        if field.key in field_vals:
            field.current_value = field_vals[field.key]

    # ── Header ───────────────────────────────────────────────────────────────
    st.subheader(f"ROI Calculator — {customer.company_name}")
    st.caption(f"{product.name} · {customer.industry} · {customer.company_size}")

    with st.expander("Why these metrics?", expanded=False):
        st.write(calculator.rationale)

    st.divider()

    # ── Input fields ─────────────────────────────────────────────────────────
    col_inputs, col_outputs = st.columns([3, 2], gap="large")

    with col_inputs:
        st.markdown("**Inputs**")
        st.caption("AI-estimated values based on your product and customer context. Adjust any value to reflect what you know about this account.")

        new_vals = {}
        for field in calculator.fields:
            current = field_vals.get(field.key, field.ai_estimate)
            col_label, col_input = st.columns([3, 2])
            with col_label:
                st.markdown(f"**{field.label}**")
                st.caption(f"{field.description}  \n*Value driver: {field.value_driver}*")
            with col_input:
                val = st.number_input(
                    field.unit,
                    value=float(current),
                    min_value=0.0,
                    step=max(1.0, float(current) * 0.05) if current > 0 else 1.0,
                    key=f"nc_field_{field.key}",
                    label_visibility="visible",
                )
                if val != field.ai_estimate:
                    st.caption("✏️ adjusted")
                else:
                    st.caption("🤖 AI estimate")
            new_vals[field.key] = val

    # Update field overrides in state so outputs recalculate live
    st.session_state[_FIELD_VALS] = new_vals
    for field in calculator.fields:
        v = new_vals.get(field.key)
        field.current_value = v if v != field.ai_estimate else None

    # ── Output metrics ────────────────────────────────────────────────────────
    with col_outputs:
        st.markdown("**ROI Summary**")
        st.caption("Calculated from the inputs on the left. Updates as you adjust.")
        for metric in calculator.output_metrics:
            value_str = metric.format_value(calculator.fields)
            with st.container(border=True):
                st.metric(label=metric.label, value=value_str)
                st.caption(metric.description)

    st.divider()

    # ── Save scenario ─────────────────────────────────────────────────────────
    st.markdown("**Save this scenario**")
    col_name, col_save, col_restart = st.columns([4, 2, 2])

    default_name = f"{customer.company_name} — {product.name}"
    scenario_name = col_name.text_input(
        "Scenario name",
        value=default_name,
        label_visibility="collapsed",
        placeholder="Scenario name",
    )

    if col_save.button("💾  Save", type="primary", use_container_width=True):
        # Apply current input values to calculator fields before saving
        for field in calculator.fields:
            v = new_vals.get(field.key)
            field.current_value = v if v != field.ai_estimate else None

        scenario = Scenario(
            name=scenario_name.strip() or default_name,
            product_snapshot=product,
            source_product_id=product.id,
            customer=customer,
            calculator=calculator,
        )
        save_scenario(scenario)
        st.success(f"Saved as **{scenario.name}**")
        _reset()
        st.session_state["active_scenario_id"] = scenario.id
        st.switch_page("pages/Scenarios.py")

    if col_restart.button("Start Over", use_container_width=True):
        _reset()
        st.rerun()


# ── Page entrypoint ───────────────────────────────────────────────────────────

step = _step()

st.header("New Calculator")
_render_progress(step)
st.divider()

if step == 1:
    _render_step1()
elif step == 2:
    _render_step2()
elif step == 3:
    _render_step3()
elif step == "calculator":
    _render_calculator()
