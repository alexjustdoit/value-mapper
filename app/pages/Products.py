import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from data.models import ProductConfig, ValueDriver
from data.store import delete_product, list_products, save_product

st.markdown("<style>[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],[data-testid='stSidebarNavLink']{display:none!important}</style>", unsafe_allow_html=True)


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


# ── Add/Edit dialog ──────────────────────────────────────────────────────────

_DIALOG_CSS = """<style>
/* Center and size the dialog */
div[data-testid="stDialog"] > div {
    width: 100vw !important;
    max-width: 100vw !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}
div[data-testid="stDialog"] > div > div[role="dialog"] {
    width: 65vw !important;
    max-width: 65vw !important;
    max-height: 88vh !important;
    overflow-y: auto !important;
    margin: 0 auto !important;
}
/* Make textareas fill available space dynamically */
div[data-testid="stDialog"] textarea {
    min-height: 14vh !important;
    height: 14vh !important;
}
</style>"""


@st.dialog("Product Config", width="large")
def _product_form(existing: ProductConfig | None = None) -> None:
    st.markdown(_DIALOG_CSS, unsafe_allow_html=True)
    is_edit = existing is not None
    label = "Save Changes" if is_edit else "Add Product"

    with st.form("product_form"):
        name = st.text_input(
            "Product Name *",
            value=existing.name if is_edit else "",
            placeholder="e.g. FlowSync, SalesIQ, DataBridge",
        )
        description = st.text_area(
            "What does it do? *",
            value=existing.description if is_edit else "",
            placeholder="Briefly describe what the product does and who uses it.",
        )
        drivers_text = st.text_area(
            "Value Drivers *  (one per line: Name | Description)",
            value=_drivers_to_text(existing.value_drivers) if is_edit else "",
            placeholder="Time Savings | Eliminates manual data entry across workflows\nCost Reduction | Reduces headcount needed for repetitive tasks",
        )
        use_cases_text = st.text_area(
            "Use Cases  (one per line, optional)",
            value="\n".join(existing.use_cases) if is_edit else "",
            placeholder="Automated invoice reconciliation\nReal-time inventory sync",
        )
        submitted = st.form_submit_button(label, type="primary", use_container_width=True)

    if submitted:
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

        if is_edit:
            product = existing.model_copy(update={
                "name": name.strip(),
                "description": description.strip(),
                "value_drivers": drivers,
                "use_cases": _parse_list(use_cases_text),
            })
        else:
            product = ProductConfig(
                name=name.strip(),
                description=description.strip(),
                value_drivers=drivers,
                use_cases=_parse_list(use_cases_text),
            )
        save_product(product)
        st.rerun()


# ── Page ─────────────────────────────────────────────────────────────────────

st.header("Product Library")
st.caption("Configure the products you represent. Saved configs load instantly when building a calculator.")

if st.button("+ Add Product", type="primary"):
    _product_form()

products = list_products()

if not products:
    st.info("No products yet. Add your first product to get started.")
else:
    st.divider()
    for product in products:
        with st.container(border=True):
            col1, col2, col3 = st.columns([5, 1, 1])
            with col1:
                st.markdown(f"**{product.name}**")
                st.caption(product.description[:140] + ("…" if len(product.description) > 140 else ""))
                driver_names = " · ".join(vd.name for vd in product.value_drivers)
                st.caption(f"Value drivers: {driver_names}")
            with col2:
                if st.button("Edit", key=f"edit_{product.id}", use_container_width=True):
                    _product_form(existing=product)
            with col3:
                if st.button("Delete", key=f"del_{product.id}", use_container_width=True):
                    st.session_state[f"confirm_del_{product.id}"] = True

            if st.session_state.get(f"confirm_del_{product.id}"):
                st.warning(f"Delete **{product.name}**? This cannot be undone.")
                c_yes, c_no = st.columns(2)
                if c_yes.button("Yes, delete", key=f"yes_del_{product.id}", use_container_width=True):
                    delete_product(product.id)
                    st.session_state.pop(f"confirm_del_{product.id}", None)
                    st.rerun()
                if c_no.button("Cancel", key=f"no_del_{product.id}", use_container_width=True):
                    st.session_state.pop(f"confirm_del_{product.id}", None)
                    st.rerun()
