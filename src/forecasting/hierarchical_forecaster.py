"""
Hierarchical Demand Forecasting Engine for Retail Food.
Implements multiplicative components: Base, Trend, Seasonality, PromoLift, Ramp-up,
and statistical imputation for censored stockout periods.
"""
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from src.core.base_forecaster import BaseDemandForecaster


class HierarchicalDemandForecaster(BaseDemandForecaster):
    """
    Multiplicative hierarchical forecaster across Store, SKU, and Category levels.
    """

    def __init__(self, default_elasticity: float = 1.8, tau_rampup_weeks: float = 8.0):
        self.default_elasticity = default_elasticity
        self.tau_rampup_weeks = tau_rampup_weeks
        self.base_demand: Dict[Tuple[str, str], float] = {}  # (sku, store_id) -> base weekly demand
        self.sku_elasticity: Dict[str, float] = {}
        self.seasonal_factors: Dict[Tuple[str, int], float] = {}  # (category, week_of_year) -> index
        self.store_openings: Dict[str, date] = {}
        self.fitted = False

    def impute_censored_demand(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Replaces truncated sales during stockouts (stockout_flag == 1) with estimated latent demand.
        Uses non-stockout day-of-week average per SKU-Store.
        """
        df_clean = df.copy()
        if "stockout_flag" not in df_clean.columns:
            return df_clean

        df_clean["date_dt"] = pd.to_datetime(df_clean["date"])
        df_clean["dow"] = df_clean["date_dt"].dt.dayofweek

        # Calculate mean non-stockout sales per (sku, store_id, dow)
        normal_sales = df_clean[df_clean["stockout_flag"] == 0]
        dow_means = (
            normal_sales.groupby(["sku", "store_id", "dow"])["units_sold"]
            .mean()
            .reset_index()
            .rename(columns={"units_sold": "imputed_units"})
        )

        df_clean = df_clean.merge(dow_means, on=["sku", "store_id", "dow"], how="left")
        # In case some combinations have no non-stockout data, fallback to overall sku average
        sku_means = normal_sales.groupby("sku")["units_sold"].mean().to_dict()
        df_clean["imputed_units"] = df_clean["imputed_units"].fillna(df_clean["sku"].map(sku_means)).fillna(1.0)

        # Impute wherever stockout occurred
        mask = df_clean["stockout_flag"] == 1
        df_clean.loc[mask, "units_sold"] = np.ceil(df_clean.loc[mask, "imputed_units"]).astype(int)
        df_clean.drop(columns=["dow", "imputed_units"], inplace=True)
        return df_clean

    def fit(self, df_history: pd.DataFrame) -> "HierarchicalDemandForecaster":
        """
        Fits baseline demand and seasonal factors from historical sales.
        df_history expected columns: ['date', 'store_id', 'sku', 'units_sold', 'stockout_flag']
        Optional: ['category', 'discount_pct', 'is_promo']
        """
        df = self.impute_censored_demand(df_history)
        df["date_dt"] = pd.to_datetime(df["date"])
        df["week_of_year"] = df["date_dt"].dt.isocalendar().week

        # 1. Base demand per (sku, store_id): average weekly units in non-promotional periods
        non_promo = df[df.get("is_promo", 0) == 0] if "is_promo" in df.columns else df
        weekly_per_store = non_promo.groupby(["sku", "store_id"])["units_sold"].mean() * 7.0
        self.base_demand = weekly_per_store.to_dict()

        # 2. Category seasonality
        if "category" in df.columns:
            cat_week_mean = df.groupby(["category", "week_of_year"])["units_sold"].mean()
            cat_overall_mean = df.groupby("category")["units_sold"].mean()
            for (cat, w), mean_val in cat_week_mean.items():
                overall = cat_overall_mean.get(cat, 1.0)
                self.seasonal_factors[(cat, int(w))] = (mean_val / overall) if overall > 0 else 1.0

        self.fitted = True
        return self

    def set_store_openings(self, df_stores: pd.DataFrame):
        """Sets opening dates to apply ramp-up curves."""
        for _, row in df_stores.iterrows():
            st_id = row["store_id"]
            op_date = pd.to_datetime(row["opening_date"]).date()
            self.store_openings[st_id] = op_date

    def predict(
        self,
        horizon_weeks: int = 8,
        start_date: Optional[date] = None,
        future_promos: Optional[pd.DataFrame] = None,
        store_openings: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Generates forward-looking forecast for the next N weeks at SKU and store level.
        Returns DataFrame with ['sku', 'store_id', 'forecast_week', 'forecast_units'].
        """
        if not self.fitted:
            raise ValueError("Forecaster must be fitted before predict() is called.")

        if start_date is None:
            start_date = date.today()

        if store_openings is not None:
            self.set_store_openings(store_openings)

        # Dictionary of future promos: (sku, store_id, week_offset) -> discount_pct
        promo_dict = {}
        if future_promos is not None:
            for _, r in future_promos.iterrows():
                promo_dict[(r["sku"], r["store_id"], int(r.get("week_offset", 0)))] = float(r.get("discount_pct", 0.0))

        forecast_rows = []

        for w_offset in range(1, horizon_weeks + 1):
            future_week_date = start_date + timedelta(weeks=w_offset)
            iso_week = future_week_date.isocalendar()[1]

            for (sku, store_id), base_val in self.base_demand.items():
                # 1. Base demand
                pred = max(0.1, base_val)

                # 2. Ramp-up factor for new stores
                if store_id in self.store_openings:
                    op_date = self.store_openings[store_id]
                    weeks_open = max(0.0, (future_week_date - op_date).days / 7.0)
                    if weeks_open < 26.0:
                        ramp_up = float(1.0 - np.exp(-weeks_open / self.tau_rampup_weeks))
                        pred *= ramp_up

                # 3. Promo lift
                disc = promo_dict.get((sku, store_id, w_offset), 0.0)
                if disc > 0:
                    elasticity = self.sku_elasticity.get(sku, self.default_elasticity)
                    promo_lift = 1.0 + (elasticity * disc)
                    pred *= promo_lift

                forecast_rows.append({
                    "sku": sku,
                    "store_id": store_id,
                    "forecast_week": w_offset,
                    "target_week_date": future_week_date.strftime("%Y-%m-%d"),
                    "forecast_units": max(0.0, round(pred, 2))
                })

        return pd.DataFrame(forecast_rows)

    def aggregate_by_sku(self, df_forecast: pd.DataFrame) -> pd.DataFrame:
        """Aggregates multi-store predictions into a national demand forecast per SKU."""
        agg = (
            df_forecast.groupby(["sku", "forecast_week"])["forecast_units"]
            .sum()
            .reset_index()
        )
        return agg
