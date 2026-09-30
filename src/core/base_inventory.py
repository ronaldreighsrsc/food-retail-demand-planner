"""
Abstract interface for inventory policy and safety stock engines.
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any


class BaseInventoryEngine(ABC):
    """Abstract Base Class for stochastic replenishment and inventory policies."""

    @abstractmethod
    def compute_policy(
        self,
        sku: str,
        weekly_demand: pd.Series,
        lead_time_days_mean: float,
        lead_time_days_std: float,
        abc_class: str
    ) -> Any:
        """Computes safety stock, ROP, and target inventory levels."""
        pass
