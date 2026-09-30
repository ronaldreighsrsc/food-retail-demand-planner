"""
Abstract interface for demand forecasting engines.
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional


class BaseDemandForecaster(ABC):
    """Abstract Base Class for time-series and hierarchical demand forecasters."""

    @abstractmethod
    def fit(self, df_history: pd.DataFrame) -> "BaseDemandForecaster":
        """
        Fit model using historical sales data.
        df_history must include ['date', 'store_id', 'sku', 'units_sold', 'stockout_flag']
        """
        pass

    @abstractmethod
    def predict(
        self,
        horizon_weeks: int,
        future_promos: Optional[pd.DataFrame] = None,
        store_openings: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Predict future weekly or daily demand across hierarchical levels.
        Returns DataFrame with ['sku', 'store_id', 'date_week', 'forecast_units']
        """
        pass
