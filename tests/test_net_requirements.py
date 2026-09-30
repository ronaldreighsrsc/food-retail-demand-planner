"""
Unit tests for NetRequirementsPlanner:
- Inventory position netting (CD + Stores + InTransit + OpenPOs)
- Gross demand horizon
- Net requirements and MOQ / Pallet rounding
- Urgency status flags
"""
import pytest
import pandas as pd
from src.replenishment.net_requirements import NetRequirementsPlanner


def test_net_requirements_calculation_with_orders():
    """Valida sugerido de compra con stock insuficiente."""
    df_products = pd.DataFrame([{
        "sku": "FOD-TEST-01",
        "product_name": "Test Product",
        "category": "Snacks",
        "abc_category": "A",
        "cogs_clp": 1000.0,
        "units_per_case": 20,
        "cases_per_pallet": 50,  # 1,000 units/pallet
        "moq_units": 1000,
        "supplier_lead_time_days": 56.0  # 8 weeks
    }])

    # Physical CD stock: 500 units
    df_cd = pd.DataFrame([{"sku": "FOD-TEST-01", "units_available": 500}])
    # Physical store stock: 500 units
    df_store = pd.DataFrame([{"sku": "FOD-TEST-01", "units_on_hand": 500}])
    # No in-transit, no open POs -> Total Net Position = 1,000 units
    df_pipeline = pd.DataFrame(columns=["sku", "units_ordered", "status"])

    # Forecast: 1,000 units / week for 8 weeks (8,000 units over lead time)
    # Review period: 2 weeks (2,000 units) -> Total Horizon Demand = 10,000 units
    df_fct = pd.DataFrame([
        {"sku": "FOD-TEST-01", "forecast_week": w, "forecast_units": 1000} for w in range(1, 9)
    ])

    # Safety Stock: 1,500 units
    df_ss = pd.DataFrame([{"sku": "FOD-TEST-01", "safety_stock_units": 1500}])

    df_res = NetRequirementsPlanner.calculate_requirements(
        df_products=df_products,
        df_cd_stock=df_cd,
        df_store_stock=df_store,
        df_pipeline_pos=df_pipeline,
        df_demand_forecast=df_fct,
        df_safety_stock=df_ss,
        review_horizon_weeks=2.0
    )

    row = df_res.iloc[0]
    assert row["net_inventory_position"] == 1000
    assert row["demand_horizon_units"] == 10000
    # Net Req = 10,000 + 1,500 - 1,000 = 10,500
    assert row["net_requirement_units"] == 10500
    # Rounded to pallets (1,000 u/pallet) -> 11 pallets = 11,000 units
    assert row["suggested_order_units"] == 11000
    assert row["suggested_order_pallets"] == 11.0
    assert row["suggested_investment_clp"] == 11000 * 1000.0


def test_net_requirements_no_purchase_when_overstocked():
    """Valida que si la posición de stock supera la demanda + SS, el requerimiento sea 0."""
    df_products = pd.DataFrame([{
        "sku": "FOD-OVER",
        "product_name": "Overstocked Product",
        "category": "Drinks",
        "abc_category": "B",
        "cogs_clp": 1500.0,
        "units_per_case": 24,
        "cases_per_pallet": 60,
        "moq_units": 1440,
        "supplier_lead_time_days": 42.0  # 6 weeks
    }])

    # 10,000 units on hand + 5,000 in transit
    df_cd = pd.DataFrame([{"sku": "FOD-OVER", "units_available": 10000}])
    df_store = pd.DataFrame([{"sku": "FOD-OVER", "units_on_hand": 5000}])
    df_pipeline = pd.DataFrame([{"sku": "FOD-OVER", "units_ordered": 5000, "status": "En Tránsito Marítimo"}])

    # Low demand: 200 units / week
    df_fct = pd.DataFrame([{"sku": "FOD-OVER", "forecast_week": w, "forecast_units": 200} for w in range(1, 9)])
    df_ss = pd.DataFrame([{"sku": "FOD-OVER", "safety_stock_units": 500}])

    df_res = NetRequirementsPlanner.calculate_requirements(
        df_products=df_products,
        df_cd_stock=df_cd,
        df_store_stock=df_store,
        df_pipeline_pos=df_pipeline,
        df_demand_forecast=df_fct,
        df_safety_stock=df_ss,
        review_horizon_weeks=2.0
    )

    row = df_res.iloc[0]
    assert row["net_requirement_units"] == 0
    assert row["suggested_order_units"] == 0
    assert "STOCK SUFICIENTE" in row["urgency_status"]
