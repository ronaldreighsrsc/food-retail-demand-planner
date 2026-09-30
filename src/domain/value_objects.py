"""
Value Objects for the Retail Food Demand Planning and Replenishment System.
Domain-Driven Design (DDD) immutable concepts.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ABCClass(str, Enum):
    A = "A"  # Top 80% sales value - High criticality (CSL 98%)
    B = "B"  # Next 15% sales value - Medium criticality (CSL 95%)
    C = "C"  # Tail 5% sales value - Low criticality (CSL 90%)


class ExpiryUrgencyTier(str, Enum):
    CRITICAL = "CRÍTICO: Liquidar Inmediato (Riesgo Merma Total)"
    ALERT = "ALERTA: Priorizar Despacho FEFO a Tiendas Top"
    HEALTHY = "SALUDABLE: Cobertura Conforme"


class POStatus(str, Enum):
    EMITIDA = "Emitida"
    PUERTO_MIAMI = "En Puerto Miami"
    TRANSITO_MARITIMO = "En Tránsito Marítimo"
    ADUANA_SAG = "Inspección SAG Aduana"
    EN_CD = "En CD"


class StoreCluster(str, Enum):
    METRO_HIGH_TRAFFIC = "Alto Tráfico Metro"
    RESIDENTIAL_PREMIUM = "Residencial Premium"
    REGIONAL_MALL = "Regional Mall"
    NEW_OPENING = "Tienda Nueva"


@dataclass(frozen=True)
class LeadTime:
    """Represents international import lead time parameters."""
    mean_days: float
    std_days: float

    @property
    def mean_weeks(self) -> float:
        return self.mean_days / 7.0

    @property
    def std_weeks(self) -> float:
        return self.std_days / 7.0


@dataclass(frozen=True)
class ServiceLevel:
    """Cycle Service Level and corresponding standard normal quantile Z."""
    csl: float
    z_score: float

    @classmethod
    def from_abc(cls, abc: str) -> "ServiceLevel":
        mapping = {
            "A": (0.98, 2.054),
            "B": (0.95, 1.645),
            "C": (0.90, 1.282),
        }
        csl, z = mapping.get(abc.upper(), (0.95, 1.645))
        return cls(csl=csl, z_score=z)


@dataclass(frozen=True)
class LogisticsDimensions:
    """Packaging and palletization specifications for international maritime shipping."""
    units_per_case: int
    cases_per_pallet: int
    volume_m3_per_case: float
    weight_kg_per_case: float

    @property
    def units_per_pallet(self) -> int:
        return self.units_per_case * self.cases_per_pallet

    @property
    def pallet_volume_m3(self) -> float:
        return self.volume_m3_per_case * self.cases_per_pallet
