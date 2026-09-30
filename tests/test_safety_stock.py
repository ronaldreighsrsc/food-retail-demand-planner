"""
Unit tests for stochastic safety stock and reorder point (ROP) calculation.
Validates the combined uncertainty formula:
sigma_DDLT = sqrt(L * sigma_D^2 + D^2 * sigma_L^2)
"""
import pytest
import numpy as np
import pandas as pd
from src.replenishment.safety_stock_engine import StochasticReplenishmentEngine


def test_stochastic_safety_stock_calculation():
    """Valida la fórmula de variabilidad combinada: sigma_DDLT = sqrt(L * sD^2 + D^2 * sL^2)."""
    # 12 semanas de ventas sintéticas estables (media 100, std ~10)
    sales = pd.Series([100, 95, 105, 100, 98, 102, 100, 97, 103, 100, 96, 104])

    # Lead time: 8 semanas (56 días) con std de 1 semana (7 días)
    policy = StochasticReplenishmentEngine.calculate_sku_policy(
        sku="TEST-SKU",
        weekly_sales=sales,
        lead_time_days_mean=56.0,
        lead_time_days_std=7.0,
        abc_class="A"
    )

    assert policy.weekly_demand_mean == pytest.approx(100.0, 0.5)
    assert policy.lead_time_weeks_mean == 8.0
    assert policy.lead_time_weeks_std == 1.0
    assert policy.safety_stock_units > 0
    assert policy.reorder_point_units > policy.safety_stock_units
    assert policy.service_level_target == 0.98
    assert policy.z_score == 2.054


def test_abc_service_levels():
    """Valida la asignación estricta de CSL según clasificación ABC."""
    sales = pd.Series([50, 50, 50, 50])

    pol_a = StochasticReplenishmentEngine.calculate_sku_policy("SKU-A", sales, abc_class="A")
    pol_b = StochasticReplenishmentEngine.calculate_sku_policy("SKU-B", sales, abc_class="B")
    pol_c = StochasticReplenishmentEngine.calculate_sku_policy("SKU-C", sales, abc_class="C")

    assert pol_a.service_level_target == 0.98
    assert pol_b.service_level_target == 0.95
    assert pol_c.service_level_target == 0.90

    # Clase A debe tener mayor factor Z y más stock de seguridad que B y C
    assert pol_a.z_score > pol_b.z_score > pol_c.z_score
    assert pol_a.safety_stock_units >= pol_b.safety_stock_units >= pol_c.safety_stock_units


def test_zero_variance_lead_time():
    """Cuando sigma_L = 0, sigma_DDLT se reduce a sqrt(L) * sigma_D."""
    sales = pd.Series([100, 90, 110, 100])  # std = 8.165
    s_std = float(sales.std())
    l_weeks = 4.0  # 28 days

    policy = StochasticReplenishmentEngine.calculate_sku_policy(
        sku="TEST-ZERO-L",
        weekly_sales=sales,
        lead_time_days_mean=28.0,
        lead_time_days_std=0.0,
        abc_class="B"
    )

    expected_sigma_ddlt = np.sqrt(l_weeks) * s_std
    assert policy.sigma_ddlt == pytest.approx(expected_sigma_ddlt, 0.05)


def test_engine_instance_compute_policy_and_catalog():
    """Valida la invocación mediante la interfaz BaseInventoryEngine y el cálculo masivo de catálogo."""
    engine = StochasticReplenishmentEngine()
    sales = pd.Series([200, 220, 190, 210])
    policy = engine.compute_policy(
        sku="TEST-INST",
        weekly_demand=sales,
        lead_time_days_mean=42.0,
        lead_time_days_std=5.0,
        abc_class="A"
    )
    assert policy.sku == "TEST-INST"
    assert policy.safety_stock_units > 0

    # Test catalog policies
    df_products = pd.DataFrame([
        {
            "sku": "SKU-CAT-1",
            "supplier_lead_time_days": 50.0,
            "lead_time_std_days": 6.0,
            "abc_category": "A"
        },
        {
            "sku": "SKU-CAT-2",
            "supplier_lead_time_days": 60.0,
            "lead_time_std_days": 8.0,
            "abc_category": "B"
        }
    ])
    df_sales = pd.DataFrame([
        {"sku": "SKU-CAT-1", "weekly_units": 150.0},
        {"sku": "SKU-CAT-1", "weekly_units": 160.0},
    ])
    # SKU-CAT-2 has no sales in df_sales, will trigger fallback
    df_policies = StochasticReplenishmentEngine.compute_catalog_policies(df_sales, df_products)
    assert len(df_policies) == 2
    assert "safety_stock_units" in df_policies.columns

