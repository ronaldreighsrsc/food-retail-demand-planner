"""
Analytical SQL Queries and CTEs for Executive S&OP Reporting and Dashboard.
Includes window functions, store-level inventory coverage, stockout auditing,
and GMROI analytics.
"""
import sqlite3
from typing import Optional
import pandas as pd


class AnalyticalQueries:
    """Provides high-performance analytical SQL queries on SQLite WAL database."""

    @staticmethod
    def get_store_inventory_health(conn: sqlite3.Connection, days_back: int = 30) -> pd.DataFrame:
        """
        Calculates store-level stock coverage, in-stock rate %, and operational status.
        Implements Section 11 SQL specification from design document.
        """
        sql = f"""
        WITH StorePerformance AS (
            SELECT 
                s.store_id,
                s.store_name,
                s.cluster_id,
                p.category,
                p.sku,
                p.product_name,
                AVG(f.units_sold) AS avg_daily_sales,
                SUM(CASE WHEN f.stockout_flag = 1 THEN 1 ELSE 0 END) AS stockout_days,
                COUNT(f.date) AS total_tracked_days
            FROM fct_sales_daily f
            JOIN dim_stores s ON f.store_id = s.store_id
            JOIN dim_products p ON f.sku = p.sku
            WHERE f.date >= DATE((SELECT MAX(date) FROM fct_sales_daily), '-{days_back} days')
            GROUP BY s.store_id, s.store_name, s.cluster_id, p.category, p.sku, p.product_name
        ),
        InventoryStatus AS (
            SELECT 
                store_id,
                sku,
                units_on_hand
            FROM fct_inventory_store
        )
        SELECT 
            sp.store_name,
            sp.cluster_id,
            sp.category,
            sp.sku,
            sp.product_name,
            ROUND(sp.avg_daily_sales, 2) AS daily_velocity,
            COALESCE(inv.units_on_hand, 0) AS current_stock,
            ROUND(
                CASE 
                    WHEN sp.avg_daily_sales > 0 THEN COALESCE(inv.units_on_hand, 0) / sp.avg_daily_sales 
                    ELSE 999 
                END, 1
            ) AS days_of_coverage,
            ROUND((1.0 - (CAST(sp.stockout_days AS FLOAT) / sp.total_tracked_days)) * 100.0, 1) AS in_stock_rate_pct,
            CASE 
                WHEN COALESCE(inv.units_on_hand, 0) = 0 THEN 'QUIEBRE CRÍTICO'
                WHEN (COALESCE(inv.units_on_hand, 0) / NULLIF(sp.avg_daily_sales, 0)) < 7.0 THEN 'RIESGO DE REPOSICION'
                WHEN (COALESCE(inv.units_on_hand, 0) / NULLIF(sp.avg_daily_sales, 0)) > 45.0 THEN 'SOBRESTOCK'
                ELSE 'SALUDABLE'
            END AS operational_inventory_status
        FROM StorePerformance sp
        LEFT JOIN InventoryStatus inv ON sp.store_id = inv.store_id AND sp.sku = inv.sku
        ORDER BY days_of_coverage ASC;
        """
        return pd.read_sql_query(sql, conn)

    @staticmethod
    def get_category_gmroi_analytics(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Calculates GMROI (Gross Margin Return on Investment), margin %, and inventory turnover
        by Category and Brand.
        """
        sql = """
        WITH AnnualSales AS (
            SELECT 
                p.category,
                p.brand,
                p.sku,
                p.product_name,
                p.cogs_clp,
                p.retail_price_clp,
                SUM(f.units_sold) AS total_units_sold,
                SUM(f.revenue_clp) AS total_revenue_clp,
                SUM(f.units_sold * p.cogs_clp) AS total_cogs_clp
            FROM fct_sales_daily f
            JOIN dim_products p ON f.sku = p.sku
            GROUP BY p.category, p.brand, p.sku, p.product_name, p.cogs_clp, p.retail_price_clp
        ),
        CurrentValuation AS (
            SELECT 
                sku,
                SUM(units_available) AS cd_stock_units
            FROM fct_inventory_cd
            GROUP BY sku
        )
        SELECT 
            s.category,
            s.brand,
            s.sku,
            s.product_name,
            s.total_units_sold,
            ROUND(s.total_revenue_clp, 0) AS total_revenue_clp,
            ROUND(s.total_cogs_clp, 0) AS total_cogs_clp,
            ROUND(s.total_revenue_clp - s.total_cogs_clp, 0) AS gross_margin_clp,
            ROUND(((s.total_revenue_clp - s.total_cogs_clp) / NULLIF(s.total_revenue_clp, 0)) * 100.0, 1) AS gross_margin_pct,
            COALESCE(v.cd_stock_units, 0) AS cd_stock_units,
            ROUND(COALESCE(v.cd_stock_units, 0) * s.cogs_clp, 0) AS inventory_valuation_clp,
            ROUND(s.total_units_sold / NULLIF(v.cd_stock_units, 0), 2) AS inventory_turns,
            ROUND(
                ((s.total_revenue_clp - s.total_cogs_clp) / NULLIF(v.cd_stock_units * s.cogs_clp, 0)),
                2
            ) AS gmroi
        FROM AnnualSales s
        LEFT JOIN CurrentValuation v ON s.sku = v.sku
        ORDER BY gmroi DESC;
        """
        return pd.read_sql_query(sql, conn)

    @staticmethod
    def get_regional_summary(conn: sqlite3.Connection) -> pd.DataFrame:
        """Summarizes sales and in-stock rates by geographical region."""
        sql = """
        SELECT 
            s.region_id,
            s.cluster_id,
            COUNT(DISTINCT s.store_id) AS store_count,
            SUM(f.units_sold) AS total_units_sold,
            ROUND(SUM(f.revenue_clp), 0) AS total_revenue_clp,
            ROUND((1.0 - (CAST(SUM(f.stockout_flag) AS FLOAT) / COUNT(*))) * 100.0, 2) AS regional_in_stock_rate_pct
        FROM fct_sales_daily f
        JOIN dim_stores s ON f.store_id = s.store_id
        GROUP BY s.region_id, s.cluster_id
        ORDER BY total_revenue_clp DESC;
        """
        return pd.read_sql_query(sql, conn)
