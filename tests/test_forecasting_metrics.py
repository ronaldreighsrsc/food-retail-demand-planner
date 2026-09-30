"""
Unit tests for demand forecasting accuracy metrics (WAPE, MAPE, Bias %, Tracking Signal).
"""
import pytest
import numpy as np
import pandas as pd
from src.forecasting.accuracy_metrics import ForecastQualityAuditor


def test_wape_and_bias_exact_values():
    """Valida el cálculo de WAPE y Bias frente a valores teóricos."""
    df = pd.DataFrame({
        "sku": ["SKU1", "SKU1", "SKU1"],
        "category": ["Food", "Food", "Food"],
        "actual": [100.0, 100.0, 100.0],
        "forecast": [110.0, 90.0, 130.0]
    })
    # Total actual = 300, Total forecast = 330
    # Errores = actual - forecast: [100-110=-10, 100-90=+10, 100-130=-30]
    # Errores absolutos = 10 + 10 + 30 = 50
    # WAPE = 50 / 300 * 100 = 16.67%
    # Bias % = (330 - 300) / 300 * 100 = +10.0%
    metrics = ForecastQualityAuditor.evaluate(df)
    res = metrics.iloc[0]
    assert res["wape_pct"] == pytest.approx(16.67, 0.01)
    assert res["bias_pct"] == pytest.approx(10.0, 0.01)
    assert "Balanceado" in res["bias_diagnosis"]
    assert res["is_out_of_control"] == False


def test_positive_bias_critical_diagnosis():
    """Verifica detección de sobre-pronóstico crítico (> +10%)."""
    df = pd.DataFrame({
        "sku": ["SKU-OVER"],
        "category": ["Snacks"],
        "actual": [100.0],
        "forecast": [135.0]
    })
    metrics = ForecastQualityAuditor.evaluate(df)
    res = metrics.iloc[0]
    assert res["bias_pct"] == 35.0
    assert "Sobre-pronóstico Crítico" in res["bias_diagnosis"]


def test_negative_bias_stockout_risk_diagnosis():
    """Verifica detección de sub-pronóstico severo (< -10%)."""
    df = pd.DataFrame({
        "sku": ["SKU-UNDER"],
        "category": ["Bebidas"],
        "actual": [200.0],
        "forecast": [150.0]
    })
    metrics = ForecastQualityAuditor.evaluate(df)
    res = metrics.iloc[0]
    assert res["bias_pct"] == -25.0
    assert "Sub-pronóstico Severo" in res["bias_diagnosis"]


def test_tracking_signal_out_of_control():
    """Verifica disparo de alerta si |Tracking Signal| > 4.0."""
    # 5 periodos con subestimación sistemática constante
    # actuals = [100, 100, 100, 100, 100], forecasts = [50, 50, 50, 50, 50]
    # errors = +50 en cada periodo. MAD = 50. Sum(errors) = 250.
    # TS = 250 / 50 = +5.0 (> 4.0) -> Out of control!
    df = pd.DataFrame({
        "sku": ["SKU-DRIFT"] * 5,
        "category": ["Candy"] * 5,
        "actual": [100.0] * 5,
        "forecast": [50.0] * 5
    })
    metrics = ForecastQualityAuditor.evaluate(df)
    res = metrics.iloc[0]
    assert res["tracking_signal"] == pytest.approx(5.0, 0.01)
    assert res["is_out_of_control"] == True


def test_global_kpis():
    """Verifica cálculo consolidado a nivel compañía."""
    df = pd.DataFrame({
        "sku": ["S1", "S2"],
        "actual": [100.0, 200.0],
        "forecast": [110.0, 190.0]
    })
    # Total actual = 300, Total forecast = 300 -> Bias = 0.0%
    # Abs errors = 10 + 10 = 20 -> WAPE = 20 / 300 * 100 = 6.67%
    res = ForecastQualityAuditor.calculate_global_kpis(df)
    assert res["global_bias_pct"] == 0.0
    assert res["global_wape_pct"] == pytest.approx(6.67, 0.01)
