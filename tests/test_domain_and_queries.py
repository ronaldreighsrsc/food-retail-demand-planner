"""
Unit tests for Domain models, Value Objects, Database Manager and Analytical SQL Queries.
"""
from datetime import date, timedelta
import sqlite3
import pytest
import pandas as pd
from src.domain.value_objects import (
    ABCClass,
    ExpiryUrgencyTier,
    POStatus,
    StoreCluster,
    LeadTime,
    ServiceLevel,
    LogisticsDimensions
)
from src.domain.models import Product, Store, InventoryBatch, PurchaseOrder, DailySale
from src.data.db_manager import DatabaseManager
from src.reporting.analytical_queries import AnalyticalQueries


def test_value_objects_lead_time_and_service_level():
    lt = LeadTime(mean_days=63.0, std_days=7.0)
    assert lt.mean_weeks == 9.0
    assert lt.std_weeks == 1.0

    sl_a = ServiceLevel.from_abc("A")
    assert sl_a.csl == 0.98
    assert sl_a.z_score == 2.054

    sl_b = ServiceLevel.from_abc("B")
    assert sl_b.csl == 0.95

    sl_c = ServiceLevel.from_abc("C")
    assert sl_c.csl == 0.90

    dims = LogisticsDimensions(
        units_per_case=24,
        cases_per_pallet=50,
        volume_m3_per_case=0.03,
        weight_kg_per_case=5.0
    )
    assert dims.units_per_pallet == 1200
    assert dims.pallet_volume_m3 == pytest.approx(1.5, 0.01)


def test_domain_product_and_store_properties():
    prod = Product(
        sku="SKU-TEST-01",
        product_name="Chips USA 200g",
        category="Snacks",
        sub_category="Extruidos",
        brand="Frito-Lay",
        cogs_clp=2000.0,
        retail_price_clp=4000.0,
        shelf_life_total_days=270,
        min_shelf_life_acceptance_days=150,
        units_per_case=20,
        cases_per_pallet=40,
        volume_m3_per_case=0.04,
        weight_kg_per_case=5.0,
        moq_units=800,
        supplier_lead_time_days=60.0,
        lead_time_std_days=8.0,
        abc_category="A"
    )
    assert prod.gross_margin_clp == 2000.0
    assert prod.gross_margin_pct == 0.50
    assert prod.units_per_pallet == 800
    assert prod.lead_time.mean_days == 60.0

    # Store ramp-up
    open_dt = date(2026, 8, 1)
    as_of = date(2026, 9, 30)
    st = Store(
        store_id="STR-T1",
        store_name="Tienda Test",
        city="Santiago",
        region_id="RM",
        cluster_id="Tienda Nueva",
        opening_date=open_dt,
        sales_area_m2=140.0,
        shelf_capacity_units=4000,
        transit_days_from_cd=1
    )
    assert st.weeks_since_opening(as_of) > 8.0
    factor = st.ramp_up_factor(as_of)
    assert 0.0 < factor <= 1.0


def test_database_manager_and_analytical_queries(tmp_path):
    """Prueba la creación de base de datos SQLite WAL y la ejecución de queries analíticas."""
    db_file = str(tmp_path / "test_retail.db")
    db = DatabaseManager(db_path=db_file)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        # Insert sample store
        cursor.execute("""
            INSERT INTO dim_stores VALUES 
            ('STR-01', 'Providencia', 'Santiago', 'RM', 'Alto Tráfico Metro', '2023-01-01', 150.0, 5000, 1)
        """)
        # Insert sample product
        cursor.execute("""
            INSERT INTO dim_products VALUES 
            ('SKU-1', 'Dr Pepper 355ml', 'Bebidas', 'Gaseosas', 'Dr Pepper', 1000.0, 2000.0, 365, 180, 24, 72, 0.02, 9.0, 1728, 60.0, 8.0, 'A')
        """)
        # Insert CD batch
        cursor.execute("""
            INSERT INTO fct_inventory_cd VALUES 
            ('BTC-01', 'SKU-1', 2000, 0, 2000, '2026-08-01', '2027-08-01', 'RACK-01')
        """)
        # Insert store inventory
        cursor.execute("""
            INSERT INTO fct_inventory_store VALUES 
            ('STR-01', 'SKU-1', 100, '2026-09-30')
        """)
        # Insert sales
        for d in range(10):
            cursor.execute(f"""
                INSERT INTO fct_sales_daily (date, store_id, sku, units_sold, revenue_clp, is_promo, discount_pct, stockout_flag)
                VALUES ('2026-09-{20+d}', 'STR-01', 'SKU-1', 10, 20000.0, 0, 0.0, 0)
            """)
        conn.commit()

        # Run queries
        df_health = AnalyticalQueries.get_store_inventory_health(conn, days_back=30)
        assert len(df_health) == 1
        assert df_health.iloc[0]["store_name"] == "Providencia"
        assert df_health.iloc[0]["current_stock"] == 100

        df_gmroi = AnalyticalQueries.get_category_gmroi_analytics(conn)
        assert len(df_gmroi) == 1
        assert df_gmroi.iloc[0]["sku"] == "SKU-1"
        assert df_gmroi.iloc[0]["gross_margin_pct"] == 50.0

        df_reg = AnalyticalQueries.get_regional_summary(conn)
        assert len(df_reg) == 1
        assert df_reg.iloc[0]["region_id"] == "RM"
