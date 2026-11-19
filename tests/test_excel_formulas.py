"""
Unit tests for Corporate Excel S&OP Workbook generator.
Verifies live formula syntax and workbook structure with openpyxl.
"""
import os
import openpyxl
import pandas as pd
import pytest
from src.reporting.excel_snop_builder import CorporateSnOpExcelBuilder


def test_excel_snop_builder_structure_and_formulas(tmp_path):
    """Valida la presencia de fórmulas encadenadas vivas en la planilla generada."""
    out_file = str(tmp_path / "test_snop_model.xlsx")
    CorporateSnOpExcelBuilder.build_snop_workbook(filepath=out_file)

    assert os.path.exists(out_file)
    wb = openpyxl.load_workbook(out_file, data_only=False)

    # 1. Verifica pestañas
    sheet_names = wb.sheetnames
    assert "Plan_Compras_SOP" in sheet_names
    assert "Auditoria_Forecast" in sheet_names
    assert "Monitor_Caducidad_FEFO" in sheet_names

    ws1 = wb["Plan_Compras_SOP"]

    # 2. Verifica fila de encabezados
    headers = [cell.value for cell in ws1[1]]
    assert "SKU" in headers
    assert "Requerimiento Neto" in headers
    assert "Orden Sugerida" in headers
    assert "Estatus S&OP" in headers

    # 3. Verifica fórmulas vivas en la fila 2
    row2_j = str(ws1["J2"].value)  # Posición Neta
    assert row2_j.startswith("=")
    assert "F2" in row2_j and "G2" in row2_j and "H2" in row2_j

    row2_k = str(ws1["K2"].value)  # Requerimiento Neto
    assert row2_k.startswith("=")
    assert "MAX" in row2_k

    row2_m = str(ws1["M2"].value)  # Orden Sugerida
    assert row2_m.startswith("=")
    assert "IF" in row2_m and "MAX" in row2_m

    row2_o = str(ws1["O2"].value)  # Inversión Sugerida
    assert row2_o.startswith("=")
    assert "M2*N2" in row2_o

    row2_p = str(ws1["P2"].value)  # Cobertura Semanas
    assert row2_p.startswith("=")
    assert "ROUND" in row2_p

    row2_q = str(ws1["Q2"].value)  # Estatus S&OP
    assert row2_q.startswith("=")
    assert "APROBAR COMPRA" in row2_q

    # 4. Verifica fórmulas de totales
    max_r = ws1.max_row
    total_val = str(ws1.cell(row=max_r, column=15).value)
    assert total_val.startswith("=SUM(")


def test_excel_forecast_audit_sheet_formulas(tmp_path):
    """Valida la presencia de fórmulas dinámicas en la pestaña de Auditoría de Forecast."""
    out_file = str(tmp_path / "test_audit_model.xlsx")
    df_audit = pd.DataFrame([{
        "sku": "FOD-SNK-01",
        "category": "Snacks",
        "total_actual_units": 500.0,
        "total_forecast_units": 550.0,
        "tracking_signal": 1.2,
        "bias_diagnosis": "Balanceado"
    }])
    CorporateSnOpExcelBuilder.build_snop_workbook(filepath=out_file, df_forecast_audit=df_audit)

    wb = openpyxl.load_workbook(out_file, data_only=False)
    ws2 = wb["Auditoria_Forecast"]

    row2_abs_error = str(ws2["E2"].value)
    assert row2_abs_error.startswith("=")
    assert "ABS" in row2_abs_error

    row2_wape = str(ws2["F2"].value)
    assert row2_wape.startswith("=")
    assert "ROUND" in row2_wape


def test_excel_fefo_sheet_formulas(tmp_path):
    """Valida la presencia de fórmulas de riesgo financiero en la pestaña FEFO."""
    out_file = str(tmp_path / "test_fefo_model.xlsx")
    df_fefo = pd.DataFrame([{
        "batch_id": "BTC-100",
        "sku": "FOD-BEV-01",
        "product_name": "Dr Pepper Cherry",
        "units_in_batch": 1000,
        "expiry_date": "2026-11-15",
        "days_to_expire": 45,
        "projected_demand_before_expiry": 600,
        "projected_waste_units": 400,
        "financial_waste_risk_clp": 800000.0,
        "urgency_tier": "ALERTA",
        "action_recommendation": "Despachar a Providencia"
    }])
    CorporateSnOpExcelBuilder.build_snop_workbook(filepath=out_file, df_fefo_risk=df_fefo)

    wb = openpyxl.load_workbook(out_file, data_only=False)
    ws3 = wb["Monitor_Caducidad_FEFO"]

    # Fila 2 columna J es Riesgo Financiero: =H2*I2
    row2_risk = str(ws3["J2"].value)
    assert row2_risk.startswith("=")
    assert "H2*I2" in row2_risk
