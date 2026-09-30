"""
Unit tests for S&OP capacity and working capital optimizer (Bounded Knapsack Solver)
and multi-scenario evaluator.
"""
import pytest
import pandas as pd
from src.snop.capacity_optimizer import SnOpCapacityOptimizer
from src.snop.scenario_evaluator import SnOpScenarioEvaluator


def test_capacity_solver_unconstrained_fit():
    """Cuando hay suficiente presupuesto y pallets, cumple 100% de la demanda."""
    df_demands = pd.DataFrame([
        {
            "sku": "SKU-A",
            "unconstrained_order_units": 1000,
            "cogs_clp": 1000.0,
            "units_per_pallet": 500,
            "gross_margin_pct": 0.50,
            "annual_turnover": 8.0,
            "abc_class": "A"
        },
        {
            "sku": "SKU-B",
            "unconstrained_order_units": 500,
            "cogs_clp": 2000.0,
            "units_per_pallet": 250,
            "gross_margin_pct": 0.40,
            "annual_turnover": 5.0,
            "abc_class": "B"
        }
    ])

    # Requerimiento: SKU-A = $1M, 2 pallets; SKU-B = $1M, 2 pallets -> Total = $2M, 4 pallets
    df_res, summary = SnOpCapacityOptimizer.optimize(
        df_demands=df_demands,
        max_budget_clp=5000000.0,
        max_pallet_capacity=10.0
    )

    assert summary.total_constrained_units == 1500
    assert summary.total_constrained_investment_clp == 2000000.0
    assert summary.total_constrained_pallets == 4.0
    assert summary.cut_skus_count == 0


def test_capacity_solver_budget_constraint_prioritization():
    """Valida que bajo tope de presupuesto, se priorice el SKU con mayor prioridad/GMROI."""
    df_demands = pd.DataFrame([
        {
            "sku": "SKU-HIGH-GMROI",
            "unconstrained_order_units": 1000,
            "cogs_clp": 1000.0,
            "units_per_pallet": 500,
            "gross_margin_pct": 0.55,
            "annual_turnover": 10.0,
            "abc_class": "A"  # Priority Score = (0.55 * 10) * 2.5 = 13.75
        },
        {
            "sku": "SKU-LOW-GMROI",
            "unconstrained_order_units": 1000,
            "cogs_clp": 1000.0,
            "units_per_pallet": 500,
            "gross_margin_pct": 0.20,
            "annual_turnover": 2.0,
            "abc_class": "C"  # Priority Score = (0.20 * 2) * 1.0 = 0.40
        }
    ])

    # Presupuesto solo alcanza para 1 de los dos SKUs ($1,000,000 CLP)
    df_res, summary = SnOpCapacityOptimizer.optimize(
        df_demands=df_demands,
        max_budget_clp=1000000.0,
        max_pallet_capacity=10.0
    )

    assert summary.total_constrained_investment_clp == 1000000.0
    row_high = df_res[df_res["sku"] == "SKU-HIGH-GMROI"].iloc[0]
    row_low = df_res[df_res["sku"] == "SKU-LOW-GMROI"].iloc[0]

    # SKU con alto GMROI se aprueba al 100%
    assert row_high["constrained_order_units"] == 1000
    # SKU con bajo GMROI queda cortado
    assert row_low["constrained_order_units"] == 0
    assert summary.cut_skus_count == 1


def test_scenario_evaluator():
    """Valida la generación de comparativa de escenarios S&OP."""
    df_demands = pd.DataFrame([{
        "sku": "SKU-1",
        "unconstrained_order_units": 2000,
        "cogs_clp": 1500.0,
        "units_per_pallet": 500,
        "gross_margin_pct": 0.40,
        "annual_turnover": 6.0,
        "abc_class": "A"
    }])

    df_scenarios = SnOpScenarioEvaluator.evaluate_scenarios(
        df_demands=df_demands,
        base_budget_clp=3000000.0,
        base_pallets=4.0
    )

    assert len(df_scenarios) == 5
    assert "Sin Restricciones" in df_scenarios.iloc[0]["scenario_name"]
    assert "Caja Restringida" in df_scenarios.iloc[1]["scenario_name"]


def test_capacity_solver_pallet_constraint_bottleneck():
    """Valida que cuando el cuello de botella son los pallets y no el dinero, se acote por pallets."""
    df_demands = pd.DataFrame([{
        "sku": "SKU-BULKY",
        "unconstrained_order_units": 1000,
        "cogs_clp": 100.0,
        "units_per_pallet": 100,  # 10 pallets needed
        "gross_margin_pct": 0.50,
        "annual_turnover": 5.0,
        "abc_class": "A"
    }])

    # Budget $1,000,000 (enough for 10,000 units), but max pallets = 2.0 (only 200 units fit)
    df_res, summary = SnOpCapacityOptimizer.optimize(
        df_demands=df_demands,
        max_budget_clp=1000000.0,
        max_pallet_capacity=2.0
    )
    # Units should be capped to 200 (or rounded multiple of 12)
    assert summary.total_constrained_pallets <= 2.0
    assert summary.total_constrained_units <= 200
    assert summary.warehouse_pallet_utilization_pct <= 100.0

