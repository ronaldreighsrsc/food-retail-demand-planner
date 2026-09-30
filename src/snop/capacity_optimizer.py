"""
S&OP Capacity and Working Capital Constrained Optimizer.
Solves the Bounded Knapsack Allocation problem prioritizing by GMROI and Service Criticality (ABC).
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from src.core.base_snop import BaseSnOpOptimizer


@dataclass(frozen=True)
class SnOpPlanSummary:
    total_unconstrained_units: int
    total_unconstrained_investment_clp: float
    total_unconstrained_pallets: float
    total_constrained_units: int
    total_constrained_investment_clp: float
    total_constrained_pallets: float
    budget_utilization_pct: float
    warehouse_pallet_utilization_pct: float
    average_projected_gmroi: float
    cut_skus_count: int
    partially_filled_skus_count: int


class SnOpCapacityOptimizer(BaseSnOpOptimizer):
    """
    Optimizes purchase order execution within executive working capital ($)
    and physical central warehouse space (pallets / m3) constraints.
    """

    @classmethod
    def optimize(
        cls,
        df_demands: pd.DataFrame,
        max_budget_clp: float,
        max_pallet_capacity: float
    ) -> Tuple[pd.DataFrame, SnOpPlanSummary]:
        """
        df_demands must contain:
        ['sku', 'unconstrained_order_units', 'cogs_clp', 'units_per_pallet',
         'gross_margin_pct', 'annual_turnover', 'abc_class']
        Optional: ['units_per_case', 'product_name', 'category']
        """
        df = df_demands.copy()

        # Fill default values if columns are missing
        if "gross_margin_pct" not in df.columns:
            df["gross_margin_pct"] = 0.45
        if "annual_turnover" not in df.columns:
            # Turnover estimation by ABC: A=8.5, B=5.0, C=2.5
            abc_turns = {"A": 8.5, "B": 5.0, "C": 2.5}
            df["annual_turnover"] = df["abc_class"].map(abc_turns).fillna(5.0)

        # 1. Projected GMROI = Gross Margin % * Annual Turnover
        df["projected_gmroi"] = df["gross_margin_pct"] * df["annual_turnover"]

        # 2. Resource consumption of unconstrained demand
        df["units_per_pallet"] = df["units_per_pallet"].replace(0, 1000)
        df["unconstrained_pallets"] = df["unconstrained_order_units"] / df["units_per_pallet"]
        df["unconstrained_cost_clp"] = df["unconstrained_order_units"] * df["cogs_clp"]

        # 3. Priority Score: GMROI * ABC Weight
        abc_weight = {"A": 2.5, "B": 1.5, "C": 1.0}
        df["priority_score"] = df["projected_gmroi"] * df["abc_class"].map(abc_weight).fillna(1.0)

        # Sort descending by priority score
        df = df.sort_values(by="priority_score", ascending=False).reset_index(drop=True)

        current_budget = 0.0
        current_pallets = 0.0
        constrained_units = []
        cut_count = 0
        partial_count = 0

        for _, row in df.iterrows():
            units_wanted = int(row["unconstrained_order_units"])
            unit_cogs = float(row["cogs_clp"])
            pallet_units = float(row["units_per_pallet"])
            units_case = int(row.get("units_per_case", 24))

            if units_wanted == 0:
                constrained_units.append(0)
                continue

            cost_order = units_wanted * unit_cogs
            pallets_order = units_wanted / pallet_units

            # Can we fulfill 100% of this order?
            if (current_budget + cost_order <= max_budget_clp) and (current_pallets + pallets_order <= max_pallet_capacity):
                allocated = units_wanted
            else:
                # Fractional allocation bounded by tightest bottleneck
                budget_remaining = max(0.0, max_budget_clp - current_budget)
                pallets_remaining = max(0.0, max_pallet_capacity - current_pallets)

                units_by_budget = int(budget_remaining // unit_cogs)
                units_by_pallets = int(pallets_remaining * pallet_units)

                allocated = max(0, min(units_wanted, units_by_budget, units_by_pallets))
                # Round to nearest case if possible
                if allocated >= units_case:
                    allocated = int((allocated // units_case) * units_case)

                if allocated == 0:
                    cut_count += 1
                elif allocated < units_wanted:
                    partial_count += 1

            current_budget += allocated * unit_cogs
            current_pallets += allocated / pallet_units
            constrained_units.append(allocated)

        df["constrained_order_units"] = constrained_units
        df["constrained_cost_clp"] = df["constrained_order_units"] * df["cogs_clp"]
        df["constrained_pallets"] = df["constrained_order_units"] / df["units_per_pallet"]
        df["fulfillment_pct"] = np.where(
            df["unconstrained_order_units"] > 0,
            (df["constrained_order_units"] / df["unconstrained_order_units"]) * 100.0,
            100.0
        )

        summary = SnOpPlanSummary(
            total_unconstrained_units=int(df["unconstrained_order_units"].sum()),
            total_unconstrained_investment_clp=float(df["unconstrained_cost_clp"].sum()),
            total_unconstrained_pallets=round(float(df["unconstrained_pallets"].sum()), 1),
            total_constrained_units=int(df["constrained_order_units"].sum()),
            total_constrained_investment_clp=round(current_budget, 0),
            total_constrained_pallets=round(current_pallets, 1),
            budget_utilization_pct=round((current_budget / max_budget_clp) * 100.0, 2) if max_budget_clp > 0 else 0.0,
            warehouse_pallet_utilization_pct=round((current_pallets / max_pallet_capacity) * 100.0, 2) if max_pallet_capacity > 0 else 0.0,
            average_projected_gmroi=round(float(df["projected_gmroi"].mean()), 2),
            cut_skus_count=cut_count,
            partially_filled_skus_count=partial_count
        )

        return df, summary
