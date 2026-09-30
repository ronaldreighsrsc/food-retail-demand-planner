"""
Shelf-Life, FEFO Dispatch and Biological Expiration Risk Monitor.
Detects lots with imminent expiration risk, calculates biological waste units,
computes financial loss in CLP, and provides capillary redistribution recommendations.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


@dataclass
class ExpiryRiskReport:
    batch_id: str
    sku: str
    product_name: str
    units_in_batch: int
    expiry_date: str
    days_to_expire: int
    projected_demand_before_expiry: int
    projected_waste_units: int
    financial_waste_risk_clp: float
    urgency_tier: str
    action_recommendation: str


class ShelfLifeRiskMonitor:
    """Monitors inventory batches in CD and stores under FEFO policy."""

    @staticmethod
    def evaluate_batches(
        df_batches: pd.DataFrame,
        df_daily_forecast: pd.DataFrame,
        as_of_date: Optional[date] = None,
        cogs_map: Optional[Dict[str, float]] = None,
        product_name_map: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Evaluates batches against forward-looking daily sales forecast.
        """
        if as_of_date is None:
            as_of_date = date(2026, 9, 30)

        as_of_dt = pd.to_datetime(as_of_date)

        # Precalculate daily run rate per SKU from forecast
        daily_rates = {}
        if not df_daily_forecast.empty:
            for sku, group in df_daily_forecast.groupby("sku"):
                daily_rates[sku] = float(group["forecast_units"].mean())

        reports = []
        for _, row in df_batches.iterrows():
            batch_id = str(row["batch_id"])
            sku = str(row["sku"])
            p_name = product_name_map.get(sku, row.get("product_name", sku)) if product_name_map else row.get("product_name", sku)
            units = int(row.get("units_available", row.get("units_on_hand", 0)))
            exp_date = pd.to_datetime(row["expiry_date"])
            unit_cogs = float(cogs_map.get(sku, row.get("cogs_clp", 2000.0))) if cogs_map else float(row.get("cogs_clp", 2000.0))

            days_remaining = int((exp_date - as_of_dt).days)

            # Daily run rate across the chain
            daily_run_rate = max(0.5, daily_rates.get(sku, 5.0))

            # Projected sales before expiry
            projected_sales = int(max(0, days_remaining * daily_run_rate))
            waste_units = max(0, units - projected_sales) if days_remaining > 0 else units
            waste_clp = waste_units * unit_cogs

            # Categorize urgency tier
            if days_remaining <= 45 or waste_units > 0:
                tier = "CRÍTICO: Liquidar Inmediato (Riesgo Merma Total)"
                recommendation = f"Activar 30% descuento promocional o transferir {waste_units} u. a sucursales Metro de alto flujo."
            elif days_remaining <= 90:
                tier = "ALERTA: Priorizar Despacho FEFO a Tiendas Top"
                recommendation = "Bloquear despacho de lotes más nuevos; forzar salida prioritaria FEFO a Providencia y Las Condes."
            else:
                tier = "SALUDABLE: Cobertura Conforme"
                recommendation = "Flujo normal de abastecimiento CD a tiendas."

            reports.append(ExpiryRiskReport(
                batch_id=batch_id,
                sku=sku,
                product_name=str(p_name),
                units_in_batch=units,
                expiry_date=exp_date.strftime("%Y-%m-%d"),
                days_to_expire=days_remaining,
                projected_demand_before_expiry=projected_sales,
                projected_waste_units=waste_units,
                financial_waste_risk_clp=round(waste_clp, 0),
                urgency_tier=tier,
                action_recommendation=recommendation
            ))

        df_rep = pd.DataFrame([r.__dict__ for r in reports])
        return df_rep.sort_values(by=["financial_waste_risk_clp", "days_to_expire"], ascending=[False, True]).reset_index(drop=True)
