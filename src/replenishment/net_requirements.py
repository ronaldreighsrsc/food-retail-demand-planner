"""
Net Requirements Planning (MRP / Sugerido de Compra) for International Food Imports.
Incorporates On-Hand inventory (CD + Stores), Maritime in-transit, Open POs, MOQ,
and pallet containerization.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class NetRequirementItem:
    sku: str
    product_name: str
    category: str
    abc_class: str
    cogs_clp: float
    units_per_pallet: int
    moq_units: int
    supplier_lead_time_days: float
    stock_cd: int
    stock_stores: int
    in_transit: int
    open_pos: int
    net_inventory_position: int
    demand_horizon_units: float
    safety_stock_units: int
    net_requirement_units: int
    suggested_order_units: int
    suggested_order_pallets: float
    suggested_investment_clp: float
    days_of_stock_on_hand: float
    urgency_status: str


class NetRequirementsPlanner:
    """
    Computes net purchase order recommendations for USA import suppliers.
    """

    @classmethod
    def calculate_requirements(
        cls,
        df_products: pd.DataFrame,
        df_cd_stock: pd.DataFrame,
        df_store_stock: pd.DataFrame,
        df_pipeline_pos: pd.DataFrame,
        df_demand_forecast: pd.DataFrame,
        df_safety_stock: pd.DataFrame,
        review_horizon_weeks: float = 2.0
    ) -> pd.DataFrame:
        """
        Calculates net requirements and containerized purchase recommendations.
        """
        # 1. Total CD on-hand
        cd_stock = df_cd_stock.groupby("sku")["units_available"].sum().to_dict()

        # 2. Total Stores on-hand
        store_stock = df_store_stock.groupby("sku")["units_on_hand"].sum().to_dict()

        # 3. Pipeline OCs split: in-transit vs open
        pipeline_status = df_pipeline_pos.copy()
        in_transit_mask = pipeline_status["status"].isin(["En Tránsito Marítimo", "Inspección SAG Aduana"])
        open_pos_mask = pipeline_status["status"].isin(["Emitida", "En Puerto Miami"])

        in_transit_by_sku = pipeline_status[in_transit_mask].groupby("sku")["units_ordered"].sum().to_dict()
        open_pos_by_sku = pipeline_status[open_pos_mask].groupby("sku")["units_ordered"].sum().to_dict()

        # 4. Safety stock by SKU
        ss_by_sku = df_safety_stock.set_index("sku")["safety_stock_units"].to_dict()

        # 5. Weekly run rate / forecast
        # Demand over L + R weeks
        forecast_by_sku = df_demand_forecast.groupby("sku")["forecast_units"].sum().to_dict()
        weeks_in_forecast = max(1, df_demand_forecast["forecast_week"].max()) if "forecast_week" in df_demand_forecast.columns else 8

        results = []
        for _, prod in df_products.iterrows():
            sku = prod["sku"]
            p_name = prod["product_name"]
            cat = prod["category"]
            abc = prod.get("abc_category", "A")
            cogs = float(prod["cogs_clp"])
            u_case = int(prod["units_per_case"])
            c_pallet = int(prod["cases_per_pallet"])
            units_pallet = max(1, u_case * c_pallet)
            moq = int(prod.get("moq_units", units_pallet))
            lead_time_days = float(prod.get("supplier_lead_time_days", 60.0))
            lead_time_weeks = lead_time_days / 7.0

            s_cd = int(cd_stock.get(sku, 0))
            s_str = int(store_stock.get(sku, 0))
            trans = int(in_transit_by_sku.get(sku, 0))
            open_po = int(open_pos_by_sku.get(sku, 0))

            # Total inventory position
            inv_position = s_cd + s_str + trans + open_po

            # Weekly demand rate
            total_fct = forecast_by_sku.get(sku, 500.0)
            weekly_rate = total_fct / weeks_in_forecast
            daily_rate = max(0.1, weekly_rate / 7.0)

            # Demand over Lead Time + Review Horizon
            demand_horizon = (lead_time_weeks + review_horizon_weeks) * weekly_rate
            ss = int(ss_by_sku.get(sku, np.ceil(weekly_rate * 2.0)))

            # Net Requirement = max(0, Demand(L+R) + SS - Net_Position)
            gross_needed = demand_horizon + ss
            net_req = max(0, int(np.ceil(gross_needed - inv_position)))

            # Pallet and MOQ rounding
            if net_req > 0:
                target_units = max(net_req, moq)
                suggested_order = int(np.ceil(target_units / units_pallet) * units_pallet)
            else:
                suggested_order = 0

            suggested_pallets = round(suggested_order / units_pallet, 2)
            suggested_inv = round(suggested_order * cogs, 0)

            # Days of stock currently physically available (CD + Stores)
            physical_stock = s_cd + s_str
            dos = round(physical_stock / daily_rate, 1)

            # Urgency status
            if dos < lead_time_days:
                urgency = "CRÍTICO: Quiebre Antes de Arribo (DOS < Lead Time)"
            elif dos < (lead_time_days + review_horizon_weeks * 7):
                urgency = "REORDEN REQUERIDO: En Ventana de Compra"
            else:
                urgency = "STOCK SUFICIENTE: Cobertura Óptima"

            results.append(NetRequirementItem(
                sku=sku,
                product_name=p_name,
                category=cat,
                abc_class=abc,
                cogs_clp=cogs,
                units_per_pallet=units_pallet,
                moq_units=moq,
                supplier_lead_time_days=lead_time_days,
                stock_cd=s_cd,
                stock_stores=s_str,
                in_transit=trans,
                open_pos=open_po,
                net_inventory_position=inv_position,
                demand_horizon_units=round(demand_horizon, 1),
                safety_stock_units=ss,
                net_requirement_units=net_req,
                suggested_order_units=suggested_order,
                suggested_order_pallets=suggested_pallets,
                suggested_investment_clp=suggested_inv,
                days_of_stock_on_hand=dos,
                urgency_status=urgency
            ))

        return pd.DataFrame([r.__dict__ for r in results])
