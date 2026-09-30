"""
Additional coverage tests for Data Generator, DB Manager, and Models.
"""
from datetime import date
import os
import pytest
import pandas as pd
from src.data.data_generator import FoodRetailDataGenerator
from src.data.db_manager import DatabaseManager
from src.domain.models import InventoryBatch, PurchaseOrder, DailySale
from src.domain.value_objects import ExpiryUrgencyTier, POStatus, StoreCluster


def test_data_generator_components():
    gen = FoodRetailDataGenerator(seed=123)
    df_prod = gen.generate_products()
    assert len(df_prod) >= 30
    assert "sku" in df_prod.columns
    assert "cogs_clp" in df_prod.columns

    df_stores = gen.generate_stores()
    assert len(df_stores) == 52

    df_batches = gen.generate_inventory_cd(df_prod.head(5))
    assert len(df_batches) > 0
    assert "expiry_date" in df_batches.columns

    df_store_inv = gen.generate_store_inventory(df_prod.head(3), df_stores.head(3))
    assert len(df_store_inv) == 9

    df_pos = gen.generate_purchase_orders_pipeline(df_prod)
    assert len(df_pos) > 0


def test_models_methods():
    batch = InventoryBatch(
        batch_id="B-01",
        sku="SKU-1",
        product_name="Candy",
        units_on_hand=100,
        units_reserved=10,
        units_available=90,
        reception_date=date(2026, 8, 1),
        expiry_date=date(2026, 10, 14),
        pallet_location_id="LOC-1",
        cogs_clp=500.0
    )
    as_of = date(2026, 9, 30)
    assert batch.days_to_expiry(as_of) == 14
    assert batch.weeks_to_expiry(as_of) == 2.0

    po = PurchaseOrder(
        po_number="PO-01",
        sku="SKU-1",
        order_date=date(2026, 9, 1),
        units_ordered=500,
        status="En Tránsito Marítimo",
        estimated_arrival_date=date(2026, 10, 20)
    )
    assert po.is_in_pipeline is True

    po_delivered = PurchaseOrder(
        po_number="PO-02",
        sku="SKU-1",
        order_date=date(2026, 8, 1),
        units_ordered=500,
        status="En CD",
        estimated_arrival_date=date(2026, 9, 15)
    )
    assert po_delivered.is_in_pipeline is False


def test_parquet_and_read_table(tmp_path):
    db_path = str(tmp_path / "test_parquet.db")
    db = DatabaseManager(db_path=db_path)
    parquet_path = str(tmp_path / "dim_stores.parquet")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dim_stores VALUES ('STR-01', 'Test', 'City', 'RM', 'Metro', '2023-01-01', 100, 3000, 1)")
        conn.commit()

    db.export_to_parquet("dim_stores", parquet_path)
    assert os.path.exists(parquet_path)

    df_read = db.read_table("dim_stores", query_filter="store_id = 'STR-01'")
    assert len(df_read) == 1
    assert df_read.iloc[0]["store_id"] == "STR-01"
