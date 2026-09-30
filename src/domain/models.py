"""
Domain entities for Food Retail Demand Planning and Replenishment (DDD).
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from src.domain.value_objects import (
    ABCClass,
    ExpiryUrgencyTier,
    POStatus,
    StoreCluster,
    LeadTime,
    ServiceLevel,
    LogisticsDimensions,
)


@dataclass
class Product:
    sku: str
    product_name: str
    category: str
    sub_category: str
    brand: str
    cogs_clp: float
    retail_price_clp: float
    shelf_life_total_days: int
    min_shelf_life_acceptance_days: int
    units_per_case: int
    cases_per_pallet: int
    volume_m3_per_case: float
    weight_kg_per_case: float
    moq_units: int
    supplier_lead_time_days: float = 60.0
    lead_time_std_days: float = 8.0
    abc_category: str = "A"

    @property
    def units_per_pallet(self) -> int:
        return self.units_per_case * self.cases_per_pallet

    @property
    def gross_margin_clp(self) -> float:
        return self.retail_price_clp - self.cogs_clp

    @property
    def gross_margin_pct(self) -> float:
        return (self.gross_margin_clp / self.retail_price_clp) if self.retail_price_clp > 0 else 0.0

    @property
    def lead_time(self) -> LeadTime:
        return LeadTime(mean_days=self.supplier_lead_time_days, std_days=self.lead_time_std_days)

    @property
    def service_level(self) -> ServiceLevel:
        return ServiceLevel.from_abc(self.abc_category)


@dataclass
class Store:
    store_id: str
    store_name: str
    city: str
    region_id: str
    cluster_id: str
    opening_date: date
    sales_area_m2: float
    shelf_capacity_units: int
    transit_days_from_cd: int = 1

    def weeks_since_opening(self, as_of: date) -> float:
        delta_days = (as_of - self.opening_date).days
        return max(0.0, delta_days / 7.0)

    def ramp_up_factor(self, as_of: date, tau_weeks: float = 8.0) -> float:
        """
        Ramp-up factor for newly opened stores:
        RampUp(t) = 1.0 - exp(-(t - t_open) / tau)
        For stores open longer than 26 weeks, returns 1.0.
        """
        weeks = self.weeks_since_opening(as_of)
        if weeks >= 26.0:
            return 1.0
        import numpy as np
        return float(1.0 - np.exp(-weeks / tau_weeks))


@dataclass
class InventoryBatch:
    batch_id: str
    sku: str
    product_name: str
    units_on_hand: int
    units_reserved: int
    units_available: int
    reception_date: date
    expiry_date: date
    pallet_location_id: str
    cogs_clp: float

    def days_to_expiry(self, as_of: date) -> int:
        return (self.expiry_date - as_of).days

    def weeks_to_expiry(self, as_of: date) -> float:
        return self.days_to_expiry(as_of) / 7.0


@dataclass
class PurchaseOrder:
    po_number: str
    sku: str
    order_date: date
    units_ordered: int
    status: str
    estimated_arrival_date: date

    @property
    def is_in_pipeline(self) -> bool:
        """Returns True if order is active and not yet fully delivered in CD."""
        return self.status in [
            POStatus.EMITIDA.value,
            POStatus.PUERTO_MIAMI.value,
            POStatus.TRANSITO_MARITIMO.value,
            POStatus.ADUANA_SAG.value,
        ]


@dataclass
class DailySale:
    date: date
    store_id: str
    sku: str
    units_sold: int
    revenue_clp: float
    is_promo: bool
    discount_pct: float
    stockout_flag: bool
