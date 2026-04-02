"""Tests for product and scenario persistence."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from data.models import CustomerContext, ProductConfig, Scenario, ValueDriver


def _make_product(name: str = "TestProduct") -> ProductConfig:
    return ProductConfig(
        name=name,
        description="A test product",
        value_drivers=[ValueDriver(name="Time Savings", description="Saves time")],
    )


def _make_scenario(product: ProductConfig) -> Scenario:
    customer = CustomerContext(
        company_name="Acme Corp",
        industry="Technology",
        company_size="200 employees",
        pain_points=["manual processes", "slow reporting"],
    )
    return Scenario(name="Acme Test", product_snapshot=product, customer=customer)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Patch _base_dir so all store operations write to a temp directory."""
    import data.store as store_module

    def patched_base():
        return tmp_path

    with patch.object(store_module, "_base_dir", patched_base):
        yield tmp_path


class TestProductStore:
    def test_save_and_load(self, temp_data_dir):
        from data.store import load_product, save_product
        product = _make_product()
        save_product(product)
        loaded = load_product(product.id)
        assert loaded.name == product.name
        assert loaded.id == product.id

    def test_list_products(self, temp_data_dir):
        from data.store import list_products, save_product
        p1 = _make_product("Alpha")
        p2 = _make_product("Beta")
        save_product(p1)
        save_product(p2)
        products = list_products()
        assert len(products) == 2

    def test_delete_product(self, temp_data_dir):
        from data.store import delete_product, list_products, save_product
        product = _make_product()
        save_product(product)
        assert len(list_products()) == 1
        delete_product(product.id)
        assert len(list_products()) == 0

    def test_load_missing_raises(self, temp_data_dir):
        from data.store import load_product
        with pytest.raises(FileNotFoundError):
            load_product("nonexistent-id")

    def test_save_updates_timestamp(self, temp_data_dir):
        from data.store import load_product, save_product
        import time
        product = _make_product()
        save_product(product)
        original_ts = load_product(product.id).updated_at
        time.sleep(0.01)
        save_product(product)
        updated_ts = load_product(product.id).updated_at
        assert updated_ts >= original_ts


class TestScenarioStore:
    def test_save_and_load(self, temp_data_dir):
        from data.store import load_scenario, save_scenario
        product = _make_product()
        scenario = _make_scenario(product)
        save_scenario(scenario)
        loaded = load_scenario(scenario.id)
        assert loaded.name == scenario.name
        assert loaded.customer.company_name == "Acme Corp"

    def test_list_scenarios(self, temp_data_dir):
        from data.store import list_scenarios, save_scenario
        product = _make_product()
        s1 = _make_scenario(product)
        s2 = Scenario(
            name="Second",
            product_snapshot=product,
            customer=CustomerContext(
                company_name="Beta", industry="Finance",
                company_size="500", pain_points=["costs"]
            )
        )
        save_scenario(s1)
        save_scenario(s2)
        assert len(list_scenarios()) == 2

    def test_delete_scenario(self, temp_data_dir):
        from data.store import delete_scenario, list_scenarios, save_scenario
        product = _make_product()
        scenario = _make_scenario(product)
        save_scenario(scenario)
        delete_scenario(scenario.id)
        assert len(list_scenarios()) == 0
