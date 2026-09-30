"""
Unit tests for ShelfLifeRiskMonitor:
- Days to expire calculation
- Projected demand until expiration
- Biological waste and financial loss in CLP
- Urgency tier mapping
"""
import pytest
from datetime import date, timedelta
import pandas as pd
from src.replenishment.shelf_life_monitor import ShelfLifeRiskMonitor


def test_shelf_life_critical_waste():
    """Valida detección de lote con expiración inminente y merma financiera."""
    as_of = date(2026, 9, 30)

    # Lote de 1,000 unidades que vence en 20 días
    expiry_date = as_of + timedelta(days=20)
    df_batches = pd.DataFrame([{
        "batch_id": "BTC-EXP-CRIT",
        "sku": "FOD-CRIT",
        "product_name": "Salsa BBQ",
        "units_available": 1000,
        "expiry_date": expiry_date.strftime("%Y-%m-%d"),
        "cogs_clp": 2500.0
    }])

    # Run-rate proyectado de solo 10 unidades por día
    # En 20 días se proyecta vender 20 * 10 = 200 unidades
    # Merma biológica proyectada = 1000 - 200 = 800 unidades
    # Pérdida financiera = 800 * $2,500 = $2,000,000 CLP
    df_fct = pd.DataFrame([{"sku": "FOD-CRIT", "forecast_units": 10}])

    report = ShelfLifeRiskMonitor.evaluate_batches(df_batches, df_fct, as_of_date=as_of)
    res = report.iloc[0]

    assert res["days_to_expire"] == 20
    assert res["projected_demand_before_expiry"] == 200
    assert res["projected_waste_units"] == 800
    assert res["financial_waste_risk_clp"] == 2000000.0
    assert "CRÍTICO" in res["urgency_tier"]


def test_shelf_life_healthy_batch():
    """Valida lote con vida útil suficiente y sin merma proyectada."""
    as_of = date(2026, 9, 30)
    expiry_date = as_of + timedelta(days=200)

    # 500 unidades que vencen en 200 días
    df_batches = pd.DataFrame([{
        "batch_id": "BTC-HEALTHY",
        "sku": "FOD-SAFE",
        "product_name": "Dr Pepper Cherry",
        "units_available": 500,
        "expiry_date": expiry_date.strftime("%Y-%m-%d"),
        "cogs_clp": 1000.0
    }])

    # Run-rate de 20 u/día -> Proyecta vender 4,000 u. antes de vencer (sobra demanda)
    df_fct = pd.DataFrame([{"sku": "FOD-SAFE", "forecast_units": 20}])

    report = ShelfLifeRiskMonitor.evaluate_batches(df_batches, df_fct, as_of_date=as_of)
    res = report.iloc[0]

    assert res["days_to_expire"] == 200
    assert res["projected_waste_units"] == 0
    assert res["financial_waste_risk_clp"] == 0.0
    assert "SALUDABLE" in res["urgency_tier"]
