"""
Forecast Quality and Bias Auditing Module (S&OP Standards).
Computes WAPE, MAPE, Forecast Bias %, Tracking Signal, and Business Diagnoses.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForecastKPIs:
    sku: str
    category: str
    total_actual_units: float
    total_forecast_units: float
    wape_pct: float
    mape_pct: float
    bias_pct: float
    tracking_signal: float
    bias_diagnosis: str
    is_out_of_control: bool


class ForecastQualityAuditor:
    """Audits demand forecast accuracy and systematic bias under S&OP industry standards."""

    @staticmethod
    def evaluate(
        df: pd.DataFrame,
        sku_col: str = "sku",
        actual_col: str = "actual",
        forecast_col: str = "forecast",
        category_col: str = "category"
    ) -> pd.DataFrame:
        """
        Calculates WAPE, MAPE, Bias and Tracking Signal grouped by SKU and category.
        """
        results = []
        for sku, group in df.groupby(sku_col):
            actuals = group[actual_col].to_numpy(dtype=float)
            forecasts = group[forecast_col].to_numpy(dtype=float)
            category = str(group[category_col].iloc[0]) if category_col in group.columns else "General"

            total_actual = float(np.sum(actuals))
            total_forecast = float(np.sum(forecasts))
            errors = actuals - forecasts
            abs_errors = np.abs(errors)

            # 1. WAPE (Weighted Absolute Percentage Error)
            wape = (np.sum(abs_errors) / total_actual * 100.0) if total_actual > 0 else 0.0

            # 2. MAPE (Mean Absolute Percentage Error - filtering zero denominators)
            non_zero_mask = actuals > 0
            if np.any(non_zero_mask):
                mape = float(np.mean(np.abs(errors[non_zero_mask] / actuals[non_zero_mask])) * 100.0)
            else:
                mape = 0.0

            # 3. Forecast Bias %: (Forecast - Actual) / Actual * 100
            bias = ((total_forecast - total_actual) / total_actual * 100.0) if total_actual > 0 else 0.0

            # 4. Tracking Signal: Cumulative Error / MAD
            mad = float(np.mean(abs_errors))
            cumulative_error = float(np.sum(errors))
            tracking_signal = (cumulative_error / mad) if mad > 0 else 0.0

            # S&OP Business Diagnosis for Category Management
            if bias > 10.0:
                diagnosis = "Sobre-pronóstico Crítico (Riesgo Sobrestock y Merma)"
            elif bias < -10.0:
                diagnosis = "Sub-pronóstico Severo (Riesgo Quiebre y Venta Perdida)"
            else:
                diagnosis = "Balanceado (En Tolerancia S&OP ±10%)"

            out_of_control = bool(abs(tracking_signal) > 4.0)

            results.append(ForecastKPIs(
                sku=str(sku),
                category=category,
                total_actual_units=round(total_actual, 2),
                total_forecast_units=round(total_forecast, 2),
                wape_pct=round(float(wape), 2),
                mape_pct=round(float(mape), 2),
                bias_pct=round(float(bias), 2),
                tracking_signal=round(float(tracking_signal), 2),
                bias_diagnosis=diagnosis,
                is_out_of_control=out_of_control
            ))

        return pd.DataFrame([r.__dict__ for r in results])

    @staticmethod
    def calculate_global_kpis(df: pd.DataFrame, actual_col: str = "actual", forecast_col: str = "forecast") -> Dict[str, float]:
        """Calculates global company-level forecast accuracy metrics."""
        actuals = df[actual_col].to_numpy(dtype=float)
        forecasts = df[forecast_col].to_numpy(dtype=float)

        total_actual = float(np.sum(actuals))
        total_forecast = float(np.sum(forecasts))
        errors = actuals - forecasts
        abs_errors = np.abs(errors)

        wape = (np.sum(abs_errors) / total_actual * 100.0) if total_actual > 0 else 0.0
        bias = ((total_forecast - total_actual) / total_actual * 100.0) if total_actual > 0 else 0.0
        mad = float(np.mean(abs_errors))
        tracking_signal = (float(np.sum(errors)) / mad) if mad > 0 else 0.0

        return {
            "total_actual": total_actual,
            "total_forecast": total_forecast,
            "global_wape_pct": round(wape, 2),
            "global_bias_pct": round(bias, 2),
            "global_tracking_signal": round(tracking_signal, 2),
            "is_out_of_control": abs(tracking_signal) > 4.0
        }
