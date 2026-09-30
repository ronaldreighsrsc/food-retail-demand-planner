"""
Builds the official corporate Excel S&OP model from current database state.
"""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from datetime import date
from src.data.db_manager import DatabaseManager
from src.forecasting.accuracy_metrics import ForecastQualityAuditor
from src.forecasting.hierarchical_forecaster import HierarchicalDemandForecaster
from src.replenishment.safety_stock_engine import StochasticReplenishmentEngine
from src.replenishment.net_requirements import NetRequirementsPlanner
from src.replenishment.shelf_life_monitor import ShelfLifeRiskMonitor
from src.reporting.excel_snop_builder import CorporateSnOpExcelBuilder


def generate_official_workbook():
    db = DatabaseManager()
    with db.get_connection() as conn:
        df_products = pd.read_sql_query("SELECT * FROM dim_products", conn)
        df_stores = pd.read_sql_query("SELECT * FROM dim_stores", conn)
        df_batches = pd.read_sql_query("SELECT * FROM fct_inventory_cd", conn)
        df_store_inv = pd.read_sql_query("SELECT * FROM fct_inventory_store", conn)
        df_pos = pd.read_sql_query("SELECT * FROM fct_purchase_orders_pipeline", conn)
        df_recent = pd.read_sql_query("""
            SELECT date, store_id, sku, units_sold, stockout_flag, is_promo, discount_pct
            FROM fct_sales_daily
            WHERE date >= DATE((SELECT MAX(date) FROM fct_sales_daily), '-90 days')
        """, conn)
        df_sales_weekly = pd.read_sql_query("""
            SELECT 
                sku,
                strftime('%Y-%W', date) AS sales_week,
                SUM(units_sold) AS weekly_units,
                SUM(revenue_clp) AS weekly_revenue
            FROM fct_sales_daily
            GROUP BY sku, sales_week
        """, conn)

    df_policies = StochasticReplenishmentEngine.compute_catalog_policies(df_sales_weekly, df_products)

    forecaster = HierarchicalDemandForecaster()
    forecaster.fit(df_recent)
    forecaster.set_store_openings(df_stores)
    df_fct = forecaster.predict(horizon_weeks=8, start_date=date(2026, 9, 30))

    df_net_reqs = NetRequirementsPlanner.calculate_requirements(
        df_products=df_products,
        df_cd_stock=df_batches,
        df_store_stock=df_store_inv,
        df_pipeline_pos=df_pos,
        df_demand_forecast=df_fct,
        df_safety_stock=df_policies,
        review_horizon_weeks=2.0
    )

    cogs_map = df_products.set_index("sku")["cogs_clp"].to_dict()
    name_map = df_products.set_index("sku")["product_name"].to_dict()
    df_fefo = ShelfLifeRiskMonitor.evaluate_batches(
        df_batches=df_batches,
        df_daily_forecast=df_fct,
        as_of_date=date(2026, 9, 30),
        cogs_map=cogs_map,
        product_name_map=name_map
    )

    with db.get_connection() as conn:
        df_actuals_8w = pd.read_sql_query("""
            SELECT sku, SUM(units_sold) AS actual
            FROM fct_sales_daily
            WHERE date >= DATE((SELECT MAX(date) FROM fct_sales_daily), '-56 days')
            GROUP BY sku
        """, conn)
    df_fct_8w = df_fct.groupby("sku")["forecast_units"].sum().reset_index().rename(columns={"forecast_units": "forecast"})
    df_eval = df_products[["sku", "category"]].merge(df_actuals_8w, on="sku").merge(df_fct_8w, on="sku")
    df_audit = ForecastQualityAuditor.evaluate(df_eval)

    excel_out = ROOT_DIR / "data" / "excel" / "KIOS_FLOW_Plan_Compras_SOP_Oficial.xlsx"
    CorporateSnOpExcelBuilder.build_snop_workbook(
        filepath=str(excel_out),
        df_net_reqs=df_net_reqs,
        df_forecast_audit=df_audit,
        df_fefo_risk=df_fefo
    )
    print(f"Modelo Excel generado exitosamente en: {excel_out}")


if __name__ == "__main__":
    generate_official_workbook()
