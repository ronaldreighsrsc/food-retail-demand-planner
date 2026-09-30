"""
Abstract interface for S&OP capacity and capital optimization.
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Tuple, Any


class BaseSnOpOptimizer(ABC):
    """Abstract Base Class for constrained S&OP planning."""

    @abstractmethod
    def optimize(
        self,
        df_demands: pd.DataFrame,
        max_budget_clp: float,
        max_pallet_capacity: float
    ) -> Tuple[pd.DataFrame, Any]:
        """
        Solves constrained replenishment under working capital and warehouse limits.
        """
        pass
