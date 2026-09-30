"""
Stochastic Safety Stock and Reorder Point (ROP) Engine.
Accounts for combined variability in retail store weekly demand (sigma_D)
and international maritime import lead time (sigma_L).
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from scipy.stats import norm
from src.core.base_inventory import BaseInventoryEngine


@dataclass(frozen=True)
class PolicyResult:
    sku: str
    service_level_target: float
    z_score: float
    lead_time_weeks_mean: float
    lead_time_weeks_std: float
    weekly_demand_mean: float
    weekly_demand_std: float
    sigma_ddlt: float
    safety_stock_units: int
    cycle_stock_units: int
    reorder_point_units: int
    coverage_weeks: float


class StochasticReplenishmentEngine(BaseInventoryEngine):
    """
    Computes stochastic inventory parameters under joint demand and lead-time uncertainty.
    """

    SERVICE_LEVEL_MAP = {
        "A": 0.98,  # 98% in-stock for high-velocity core SKUs
        "B": 0.95,  # 95% in-stock for intermediate items
        "C": 0.90   # 90% in-stock for slow-moving tail SKUs
    }

    @classmethod
    def calculate_sku_policy(
        cls,
        sku: str,
        weekly_sales: pd.Series,
        lead_time_days_mean: float = 60.0,
        lead_time_days_std: float = 8.0,
        abc_class: str = "A",
        review_period_weeks: float = 2.0
    ) -> PolicyResult:
        # Convert lead time days to weeks
        lt_weeks_mean = float(lead_time_days_mean / 7.0)
        lt_weeks_std = float(lead_time_days_std / 7.0)

        # Sales series validation
        clean_sales = weekly_sales.dropna()
        if len(clean_sales) == 0:
            d_mean = 1.0
            d_std = 0.5
        else:
            d_mean = float(clean_sales.mean())
            d_std = float(clean_sales.std()) if len(clean_sales) > 1 else max(0.5, d_mean * 0.25)

        if np.isnan(d_std) or d_std < 0.01:
            d_std = max(0.5, d_mean * 0.25)

        csl = cls.SERVICE_LEVEL_MAP.get(abc_class.upper(), 0.95)
        z = float(norm.ppf(csl))

        # Combined DDLT Variance:
        # Var(DDLT) = L * sigma_D^2 + D^2 * sigma_L^2
        variance_ddlt = (lt_weeks_mean * (d_std ** 2)) + ((d_mean ** 2) * (lt_weeks_std ** 2))
        sigma_ddlt = float(np.sqrt(max(0.001, variance_ddlt)))

        # Safety Stock: SS = Z * sigma_DDLT
        safety_stock = int(np.ceil(z * sigma_ddlt))

        # Expected Demand during Lead Time
        expected_demand_lt = d_mean * lt_weeks_mean

        # Reorder Point: ROP = (D * L) + SS
        rop = int(np.ceil(expected_demand_lt + safety_stock))

        # Cycle Stock based on review period
        cycle_stock = int(np.ceil(d_mean * review_period_weeks))

        # Safety stock coverage in weeks
        coverage = round(safety_stock / d_mean, 2) if d_mean > 0 else 0.0

        return PolicyResult(
            sku=str(sku),
            service_level_target=csl,
            z_score=round(z, 3),
            lead_time_weeks_mean=round(lt_weeks_mean, 2),
            lead_time_weeks_std=round(lt_weeks_std, 2),
            weekly_demand_mean=round(d_mean, 2),
            weekly_demand_std=round(d_std, 2),
            sigma_ddlt=round(sigma_ddlt, 2),
            safety_stock_units=safety_stock,
            cycle_stock_units=cycle_stock,
            reorder_point_units=rop,
            coverage_weeks=coverage
        )

    def compute_policy(
        self,
        sku: str,
        weekly_demand: pd.Series,
        lead_time_days_mean: float,
        lead_time_days_std: float,
        abc_class: str
    ) -> PolicyResult:
        return self.calculate_sku_policy(
            sku=sku,
            weekly_sales=weekly_demand,
            lead_time_days_mean=lead_time_days_mean,
            lead_time_days_std=lead_time_days_std,
            abc_class=abc_class
        )

    @classmethod
    def compute_catalog_policies(
        cls,
        df_weekly_sales: pd.DataFrame,
        df_products: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Computes policies for all products in the catalog.
        df_weekly_sales must have ['sku', 'weekly_units']
        """
        results = []
        for _, prod in df_products.iterrows():
            sku = prod["sku"]
            sku_sales = df_weekly_sales[df_weekly_sales["sku"] == sku]["weekly_units"]
            if sku_sales.empty:
                # Fallback to simulated base
                sku_sales = pd.Series([100.0, 95.0, 105.0, 100.0])

            policy = cls.calculate_sku_policy(
                sku=sku,
                weekly_sales=sku_sales,
                lead_time_days_mean=float(prod.get("supplier_lead_time_days", 60.0)),
                lead_time_days_std=float(prod.get("lead_time_std_days", 8.0)),
                abc_class=str(prod.get("abc_category", "A"))
            )
            results.append(policy.__dict__)

        return pd.DataFrame(results)
