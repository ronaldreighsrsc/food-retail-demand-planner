"""
Unit tests for HierarchicalDemandForecaster:
- Censored demand imputation on stockouts
- Store ramp-up curves
- Promotional lift
- Multi-week forecasting and SKU aggregation
"""
from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest
from src.forecasting.hierarchical_forecaster import HierarchicalDemandForecaster


def test_censored_demand_imputation():
    """Valida que los quiebres de stock (stockout_flag=1) sean imputados correctamente."""
    dates = [date(2026, 9, 1) + timedelta(days=i) for i in range(14)]
    df = pd.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "store_id": ["STR-01"] * 14,
        "sku": ["SKU-TEST"] * 14,
        "units_sold": [10, 12, 11, 10, 13, 15, 14, 10, 11, 0, 0, 12, 14, 15],
        "stockout_flag": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0]
    })
    forecaster = HierarchicalDemandForecaster()
    df_clean = forecaster.impute_censored_demand(df)

    # Las filas con stockout_flag=1 antes tenían 0; ahora deben tener valor imputado > 0
    imputed_rows = df_clean[df_clean["stockout_flag"] == 1]
    assert (imputed_rows["units_sold"] > 5).all()


def test_forecaster_fit_and_predict():
    """Valida el ciclo de fit() y predict() a 4 semanas."""
    df_hist = pd.DataFrame({
        "date": ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05", "2026-09-06", "2026-09-07"],
        "store_id": ["STR-01"] * 7,
        "sku": ["SKU-A"] * 7,
        "units_sold": [20, 20, 20, 20, 20, 20, 20],  # 140 semanal
        "stockout_flag": [0] * 7,
        "is_promo": [0] * 7,
        "discount_pct": [0.0] * 7
    })

    forecaster = HierarchicalDemandForecaster()
    forecaster.fit(df_hist)
    assert forecaster.fitted is True

    df_pred = forecaster.predict(horizon_weeks=4, start_date=date(2026, 9, 30))
    assert len(df_pred) == 4
    # Como la venta semanal base es 140 y no hay ramp-up ni promo, pred ~ 140
    assert df_pred["forecast_units"].iloc[0] == pytest.approx(140.0, 1.0)


def test_store_ramp_up_factor():
    """Valida que una tienda recién inaugurada tenga factor de ramp-up gradual."""
    df_hist = pd.DataFrame({
        "date": ["2026-09-01"] * 7,
        "store_id": ["STR-NEW"] * 7,
        "sku": ["SKU-A"] * 7,
        "units_sold": [10] * 7,
        "stockout_flag": [0] * 7
    })
    forecaster = HierarchicalDemandForecaster()
    forecaster.fit(df_hist)

    # Tienda inaugurada hace 1 semana vs fecha de predicción
    df_stores = pd.DataFrame([{
        "store_id": "STR-NEW",
        "opening_date": "2026-09-23"
    }])
    forecaster.set_store_openings(df_stores)

    df_pred = forecaster.predict(horizon_weeks=1, start_date=date(2026, 9, 30))
    # Con 2 semanas de apertura y tau=8: 1 - exp(-2/8) = 1 - 0.7788 ~ 0.221
    # Demanda base es 70. 70 * 0.221 ~ 15.5
    assert df_pred["forecast_units"].iloc[0] < 30.0


def test_promotional_lift():
    """Valida el aumento en demanda cuando existe una promoción futura planeada."""
    df_hist = pd.DataFrame({
        "date": ["2026-09-01"] * 7,
        "store_id": ["STR-01"] * 7,
        "sku": ["SKU-A"] * 7,
        "units_sold": [10] * 7,  # base semanal 70
        "stockout_flag": [0] * 7
    })
    forecaster = HierarchicalDemandForecaster(default_elasticity=2.0)
    forecaster.fit(df_hist)

    # Promoción con 25% de descuento en la semana 1
    # PromoLift = 1 + (2.0 * 0.25) = 1.50 -> 70 * 1.50 = 105
    future_promos = pd.DataFrame([{
        "sku": "SKU-A",
        "store_id": "STR-01",
        "week_offset": 1,
        "discount_pct": 0.25
    }])

    df_pred = forecaster.predict(horizon_weeks=1, start_date=date(2026, 9, 30), future_promos=future_promos)
    assert df_pred["forecast_units"].iloc[0] == pytest.approx(105.0, 1.0)
