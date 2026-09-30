"""
S&OP Scenario Evaluator.
Compares Unconstrained vs Constrained scenarios across working capital,
warehouse storage space, lost sales, and GMROI.
"""
from typing import Dict, List, Any
import pandas as pd
from src.snop.capacity_optimizer import SnOpCapacityOptimizer, SnOpPlanSummary


class SnOpScenarioEvaluator:
    """Evaluates multiple S&OP operational scenarios side by side."""

    @classmethod
    def evaluate_scenarios(
        cls,
        df_demands: pd.DataFrame,
        base_budget_clp: float,
        base_pallets: float
    ) -> pd.DataFrame:
        """
        Runs sensitivity analysis:
        - Escenario 1: Sin Restricciones (Unconstrained 100%)
        - Escenario 2: Restricción Severa de Caja (-30% Budget, 100% Pallets)
        - Escenario 3: Cuello de Botella en Bodega CD (100% Budget, -40% Pallets)
        - Escenario 4: Plan S&OP Base Equilibrado (100% Budget, 100% Pallets)
        - Escenario 5: Crecimiento y Expansión (+25% Budget, +20% Pallets)
        """
        scenarios = [
            ("1. Sin Restricciones (Unconstrained)", base_budget_clp * 5.0, base_pallets * 5.0),
            ("2. Caja Restringida (-30% Presupuesto)", base_budget_clp * 0.70, base_pallets),
            ("3. Bodega Saturation (-40% Pallets)", base_budget_clp, base_pallets * 0.60),
            ("4. Plan S&OP Base (Equilibrado)", base_budget_clp, base_pallets),
            ("5. Expansión Comercial (+25% Inversión)", base_budget_clp * 1.25, base_pallets * 1.20)
        ]

        summary_rows = []
        for name, budget, pallets in scenarios:
            df_res, summ = SnOpCapacityOptimizer.optimize(
                df_demands=df_demands,
                max_budget_clp=budget,
                max_pallet_capacity=pallets
            )

            unconstrained_rev = (df_res["unconstrained_order_units"] * df_res.get("retail_price_clp", df_res["cogs_clp"] * 1.8)).sum()
            constrained_rev = (df_res["constrained_order_units"] * df_res.get("retail_price_clp", df_res["cogs_clp"] * 1.8)).sum()
            lost_sales_clp = max(0.0, unconstrained_rev - constrained_rev)

            summary_rows.append({
                "scenario_name": name,
                "budget_limit_clp": round(budget, 0),
                "pallet_limit": round(pallets, 0),
                "allocated_units": summ.total_constrained_units,
                "investment_clp": summ.total_constrained_investment_clp,
                "pallets_utilized": summ.total_constrained_pallets,
                "budget_utilization_pct": summ.budget_utilization_pct,
                "pallet_utilization_pct": summ.warehouse_pallet_utilization_pct,
                "unconstrained_units": summ.total_unconstrained_units,
                "fulfillment_rate_pct": round((summ.total_constrained_units / summ.total_unconstrained_units * 100.0), 1) if summ.total_unconstrained_units > 0 else 100.0,
                "lost_sales_potential_clp": round(lost_sales_clp, 0),
                "cut_skus": summ.cut_skus_count,
                "partially_filled_skus": summ.partially_filled_skus_count,
                "average_gmroi": summ.average_projected_gmroi
            })

        return pd.DataFrame(summary_rows)
