"""JSON-based persistence for products and scenarios."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from data.models import ProductConfig, Scenario


# ---------------------------------------------------------------------------
# SCC-aware base directory
# ---------------------------------------------------------------------------

def _get_or_create_scc_token() -> str:
    import uuid
    import streamlit as st
    if "token" not in st.query_params:
        token = st.session_state.get("_scc_token") or str(uuid.uuid4())
        st.query_params["token"] = token
    else:
        token = st.query_params["token"]
    st.session_state["_scc_token"] = token
    return token


def _base_dir() -> Path:
    from config import DATA_DIR, SCC_MODE
    if not SCC_MODE:
        return DATA_DIR
    try:
        token = _get_or_create_scc_token()
        path = DATA_DIR / token
    except Exception:
        path = DATA_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _products_dir() -> Path:
    d = _base_dir() / "products"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _scenarios_dir() -> Path:
    d = _base_dir() / "scenarios"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def save_product(product: ProductConfig) -> None:
    product.updated_at = datetime.now(timezone.utc)
    path = _products_dir() / f"{product.id}.json"
    path.write_text(product.model_dump_json(indent=2))


def load_product(product_id: str) -> ProductConfig:
    path = _products_dir() / f"{product_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Product {product_id} not found")
    return ProductConfig.model_validate_json(path.read_text())


def list_products() -> list[ProductConfig]:
    products = []
    for path in sorted(_products_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            products.append(ProductConfig.model_validate_json(path.read_text()))
        except Exception:
            pass
    return products


def delete_product(product_id: str) -> None:
    path = _products_dir() / f"{product_id}.json"
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def save_scenario(scenario: Scenario) -> None:
    scenario.updated_at = datetime.now(timezone.utc)
    path = _scenarios_dir() / f"{scenario.id}.json"
    path.write_text(scenario.model_dump_json(indent=2))


def load_scenario(scenario_id: str) -> Scenario:
    path = _scenarios_dir() / f"{scenario_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Scenario {scenario_id} not found")
    return Scenario.model_validate_json(path.read_text())


def list_scenarios() -> list[Scenario]:
    scenarios = []
    for path in sorted(_scenarios_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            scenarios.append(Scenario.model_validate_json(path.read_text()))
        except Exception:
            pass
    return scenarios


def delete_scenario(scenario_id: str) -> None:
    path = _scenarios_dir() / f"{scenario_id}.json"
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Demo seeding
# ---------------------------------------------------------------------------

def seed_demo_data() -> None:
    """Copy demo products and scenarios into the store if not already present. Idempotent."""
    from config import DEMO_PRODUCTS_DIR, DEMO_SCENARIOS_DIR

    products_dir = _products_dir()
    if DEMO_PRODUCTS_DIR.exists():
        for demo_path in DEMO_PRODUCTS_DIR.glob("*.json"):
            try:
                data = json.loads(demo_path.read_text())
                dest = products_dir / f"{data['id']}.json"
                if not dest.exists():
                    dest.write_text(demo_path.read_text())
            except Exception:
                pass

    scenarios_dir = _scenarios_dir()
    if DEMO_SCENARIOS_DIR.exists():
        for demo_path in DEMO_SCENARIOS_DIR.glob("*.json"):
            try:
                data = json.loads(demo_path.read_text())
                dest = scenarios_dir / f"{data['id']}.json"
                if not dest.exists():
                    dest.write_text(demo_path.read_text())
            except Exception:
                pass
