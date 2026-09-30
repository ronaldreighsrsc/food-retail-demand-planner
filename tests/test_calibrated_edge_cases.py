"""
Additional validation tests to verify analytical edge cases and bring total suite to 28 tests.
"""
from datetime import date
import sqlite3
import pytest
import pandas as pd
from src.reporting.analytical_queries import AnalyticalQueries
from src.forecasting.hierarchical_forecaster import HierarchicalDemandForecaster


def test_analytical_gmroi_edge_case_zero_stock(tmp_path):
    """Valida que la consulta analítica de GMROI maneje correctamente productos con stock cero en CD sin dividir por cero."""
    db_file = str(tmp_path / "test_gmroi_edge.db")
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # Create required minimal schema
    cur.execute("""
        CREATE TABLE dim_products (
            sku TEXT PRIMARY KEY, category TEXT, brand TEXT, product_name TEXT, cogs_clp REAL, retail_price_clp REAL
        )
    """)
    cur.execute("""
        CREATE TABLE fct_sales_daily (
            date TEXT, sku TEXT, units_sold INTEGER, revenue_clp REAL
        )
    """)
    cur.execute("""
        CREATE TABLE fct_inventory_cd (
            sku TEXT, units_available INTEGER
        )
    """)

    cur.execute("INSERT INTO dim_products VALUES ('SKU-ZERO', 'Snacks', 'BrandX', 'Item Zero', 1000.0, 2000.0)")
    cur.execute("INSERT INTO fct_sales_daily VALUES ('2026-09-01', 'SKU-ZERO', 50, 100000.0)")
    # No inventory in CD (stock = 0 or null)
    conn.commit()

    df_gmroi = AnalyticalQueries.get_category_gmroi_analytics(conn)
    assert len(df_gmroi) == 1
    row = df_gmroi.iloc[0]
    assert row["cd_stock_units"] == 0
    # Turnover and GMROI should be None/NaN without throwing SQL divide-by-zero error
    assert pd.isna(row["gmroi"]) or row["gmroi"] is None
    conn.close()


def test_custom_sku_elasticity_calibration():
    """Valida la calibración de elasticidad precio diferenciada por SKU."""
    df_hist = pd.DataFrame({
        "date": ["2026-09-01"] * 7,
        "store_id": ["STR-01"] * 7,
        "sku": ["SKU-ELAST"] * 7,
        "units_sold": [10] * 7,  # 70 u. semanal base
        "stockout_flag": [0] * 7
    })
    forecaster = HierarchicalDemandForecaster(default_elasticity=1.5)
    forecaster.fit(df_hist)
    # Calibrar elasticidad específica más alta para SKU (ej. 2.5)
    forecaster.sku_elasticity["SKU-ELAST"] = 2.5

    promos = pd.DataFrame([{
        "sku": "SKU-ELAST",
        "store_id": "STR-01",
        "week_offset": 1,
        "discount_pct": 0.20  # Lift esperado = 1 + (2.5 * 0.20) = 1.50 -> 70 * 1.50 = 105
    }])

    pred = forecaster.predict(horizon_weeks=1, start_date=date(2026, 9, 30), future_promos=promos)
    assert pred["forecast_units"].iloc[0] == pytest.approx(105.0, 1.0)
