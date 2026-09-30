"""
Database manager for SQLite with WAL mode and Parquet export/import.
"""
import os
import sqlite3
from pathlib import Path
from typing import Optional
import pandas as pd


class DatabaseManager:
    """Manages the SQLite analytical and operational database with WAL mode."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = str(base_dir / "data" / "processed" / "retail_food.db")
        else:
            self.db_path = db_path

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        # Enable WAL (Write-Ahead Logging) for high-performance concurrent read/write
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def init_db(self):
        """Creates the full relational schema according to the design specification."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. dim_products
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_products (
                sku TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                sub_category TEXT NOT NULL,
                brand TEXT NOT NULL,
                cogs_clp REAL NOT NULL,
                retail_price_clp REAL NOT NULL,
                shelf_life_total_days INTEGER NOT NULL,
                min_shelf_life_acceptance_days INTEGER NOT NULL,
                units_per_case INTEGER NOT NULL,
                cases_per_pallet INTEGER NOT NULL,
                volume_m3_per_case REAL NOT NULL,
                weight_kg_per_case REAL NOT NULL,
                moq_units INTEGER NOT NULL,
                supplier_lead_time_days REAL NOT NULL DEFAULT 60.0,
                lead_time_std_days REAL NOT NULL DEFAULT 8.0,
                abc_category TEXT NOT NULL DEFAULT 'A'
            );
            """)

            # 2. dim_stores
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_stores (
                store_id TEXT PRIMARY KEY,
                store_name TEXT NOT NULL,
                city TEXT NOT NULL,
                region_id TEXT NOT NULL,
                cluster_id TEXT NOT NULL,
                opening_date TEXT NOT NULL,
                sales_area_m2 REAL NOT NULL,
                shelf_capacity_units INTEGER NOT NULL,
                transit_days_from_cd INTEGER NOT NULL DEFAULT 1
            );
            """)

            # 3. fct_sales_daily
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fct_sales_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                store_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                units_sold INTEGER NOT NULL,
                revenue_clp REAL NOT NULL,
                is_promo INTEGER NOT NULL DEFAULT 0,
                discount_pct REAL NOT NULL DEFAULT 0.0,
                stockout_flag INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (store_id) REFERENCES dim_stores(store_id),
                FOREIGN KEY (sku) REFERENCES dim_products(sku)
            );
            """)

            # Indices on fct_sales_daily for fast analytics
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON fct_sales_daily(date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_sku_store ON fct_sales_daily(sku, store_id);")

            # 4. fct_inventory_cd (Batches with FEFO tracking)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fct_inventory_cd (
                batch_id TEXT PRIMARY KEY,
                sku TEXT NOT NULL,
                units_on_hand INTEGER NOT NULL,
                units_reserved INTEGER NOT NULL DEFAULT 0,
                units_available INTEGER NOT NULL,
                reception_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                pallet_location_id TEXT NOT NULL,
                FOREIGN KEY (sku) REFERENCES dim_products(sku)
            );
            """)

            # 5. fct_inventory_store
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fct_inventory_store (
                store_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                units_on_hand INTEGER NOT NULL,
                last_updated TEXT NOT NULL,
                PRIMARY KEY (store_id, sku),
                FOREIGN KEY (store_id) REFERENCES dim_stores(store_id),
                FOREIGN KEY (sku) REFERENCES dim_products(sku)
            );
            """)

            # 6. fct_purchase_orders_pipeline
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fct_purchase_orders_pipeline (
                po_number TEXT PRIMARY KEY,
                sku TEXT NOT NULL,
                order_date TEXT NOT NULL,
                units_ordered INTEGER NOT NULL,
                status TEXT NOT NULL,
                estimated_arrival_date TEXT NOT NULL,
                FOREIGN KEY (sku) REFERENCES dim_products(sku)
            );
            """)

            conn.commit()

    def export_to_parquet(self, table_name: str, parquet_path: str):
        """Dumps a SQL table to a fast compressed Parquet file."""
        with self.get_connection() as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
            df.to_parquet(parquet_path, engine="pyarrow", compression="snappy")

    def read_table(self, table_name: str, query_filter: str = "") -> pd.DataFrame:
        """Reads table into a Pandas DataFrame."""
        with self.get_connection() as conn:
            sql = f"SELECT * FROM {table_name}"
            if query_filter:
                sql += f" WHERE {query_filter}"
            return pd.read_sql_query(sql, conn)
