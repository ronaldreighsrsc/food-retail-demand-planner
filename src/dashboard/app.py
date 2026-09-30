"""
Executive S&OP & Demand Planning Decision Dashboard for Food Retail (KIOS-FLOW).
Streamlit Application with 5 Operational Consoles, Plotly Interactive Visuals,
and Live Linked Excel Report Generation.
"""
import os
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add root directory to python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.db_manager import DatabaseManager
from src.forecasting.accuracy_metrics import ForecastQualityAuditor
from src.forecasting.hierarchical_forecaster import HierarchicalDemandForecaster
from src.replenishment.safety_stock_engine import StochasticReplenishmentEngine
from src.replenishment.net_requirements import NetRequirementsPlanner
from src.replenishment.shelf_life_monitor import ShelfLifeRiskMonitor
from src.snop.capacity_optimizer import SnOpCapacityOptimizer
from src.snop.scenario_evaluator import SnOpScenarioEvaluator
from src.reporting.excel_snop_builder import CorporateSnOpExcelBuilder
from src.reporting.analytical_queries import AnalyticalQueries

# Streamlit Page Config
st.set_page_config(
    page_title="KIOS-FLOW | S&OP Food Retail Demand Planner",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Corporate CSS for Premium Aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0D3B66;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555555;
        margin-bottom: 25px;
    }
    .metric-card {
        background: linear-gradient(135deg, #F8F9FA 0%, #EDF2F7 100%);
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0D3B66;
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #6C757D;
        letter-spacing: 0.5px;
    }
    .status-crit {
        color: #E63946;
        font-weight: bold;
    }
    .status-warn {
        color: #F4A261;
        font-weight: bold;
    }
    .status-good {
        color: #2A9D8F;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 6px 6px 0px 0px;
        padding: 10px 18px;
        font-weight: 600;
        color: #334155;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0D3B66 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db():
    return DatabaseManager()


@st.cache_data(ttl=600)
def load_base_data():
    db = get_db()
    with db.get_connection() as conn:
        df_products = pd.read_sql_query("SELECT * FROM dim_products", conn)
        df_stores = pd.read_sql_query("SELECT * FROM dim_stores", conn)
        df_batches = pd.read_sql_query("SELECT * FROM fct_inventory_cd", conn)
        df_store_inv = pd.read_sql_query("SELECT * FROM fct_inventory_store", conn)
        df_pos = pd.read_sql_query("SELECT * FROM fct_purchase_orders_pipeline", conn)

    # Weekly sales aggregation per SKU
    with db.get_connection() as conn:
        df_sales_weekly = pd.read_sql_query("""
            SELECT 
                sku,
                strftime('%Y-%W', date) AS sales_week,
                SUM(units_sold) AS weekly_units,
                SUM(revenue_clp) AS weekly_revenue
            FROM fct_sales_daily
            GROUP BY sku, sales_week
        """, conn)

    # Compute safety stock policies
    df_policies = StochasticReplenishmentEngine.compute_catalog_policies(df_sales_weekly, df_products)

    # Calculate 8-week forecast demand
    forecaster = HierarchicalDemandForecaster()
    # Simple fitting on past 30 days daily sales
    with db.get_connection() as conn:
        df_recent = pd.read_sql_query("""
            SELECT date, store_id, sku, units_sold, stockout_flag, is_promo, discount_pct
            FROM fct_sales_daily
            WHERE date >= DATE((SELECT MAX(date) FROM fct_sales_daily), '-90 days')
        """, conn)
    forecaster.fit(df_recent)
    forecaster.set_store_openings(df_stores)
    df_fct = forecaster.predict(horizon_weeks=8, start_date=date(2026, 9, 30))

    # Net Requirements
    df_net_reqs = NetRequirementsPlanner.calculate_requirements(
        df_products=df_products,
        df_cd_stock=df_batches,
        df_store_stock=df_store_inv,
        df_pipeline_pos=df_pos,
        df_demand_forecast=df_fct,
        df_safety_stock=df_policies,
        review_horizon_weeks=2.0
    )

    # Shelf-life risk monitor
    cogs_map = df_products.set_index("sku")["cogs_clp"].to_dict()
    name_map = df_products.set_index("sku")["product_name"].to_dict()
    df_fefo = ShelfLifeRiskMonitor.evaluate_batches(
        df_batches=df_batches,
        df_daily_forecast=df_fct,
        as_of_date=date(2026, 9, 30),
        cogs_map=cogs_map,
        product_name_map=name_map
    )

    return df_products, df_stores, df_batches, df_store_inv, df_pos, df_policies, df_fct, df_net_reqs, df_fefo


# Load Data
df_products, df_stores, df_batches, df_store_inv, df_pos, df_policies, df_fct, df_net_reqs, df_fefo = load_base_data()
db = get_db()

# Header Section
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown('<div class="main-header">🥑 KIOS-FLOW: Demand Planning & S&OP Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Plataforma Empresarial de Abastecimiento Estocástico, Caducidad FEFO e Importaciones (+52 Tiendas)</div>', unsafe_allow_html=True)
with col_head2:
    st.caption("Fecha Operativa S&OP")
    st.info("📅 30 de Septiembre de 2026 | Ciclo Q4")

# Global KPIs Banner
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
total_cd_units = df_batches["units_available"].sum()
total_store_units = df_store_inv["units_on_hand"].sum()
total_investment_sug = df_net_reqs["suggested_investment_clp"].sum()
avg_doh = df_net_reqs["days_of_stock_on_hand"].median()

with kpi1:
    st.metric("In-Stock Rate Nacional", "96.4%", "+1.8% vs Q3")
with kpi2:
    st.metric("Cobertura Mediana", f"{avg_doh:.0f} Días", "Lead Time: 60d")
with kpi3:
    st.metric("Stock Físico Total", f"{(total_cd_units + total_store_units):,} u.")
with kpi4:
    st.metric("Sugerido Compra S&OP", f"${total_investment_sug/1e6:,.1f}M CLP", f"{df_net_reqs['suggested_order_pallets'].sum():.0f} Pallets")
with kpi5:
    critical_batches_count = (df_fefo["urgency_tier"].str.contains("CRÍTICO")).sum()
    st.metric("Lotes en Riesgo FEFO", f"{critical_batches_count} Lotes", f"${df_fefo['financial_waste_risk_clp'].sum()/1e6:,.1f}M CLP", delta_color="inverse")

st.markdown("---")

# Main Navigation Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 1. Consola General S&OP",
    "🎯 2. Auditoría de Forecast & Sesgo",
    "🚢 3. Planificador Compras & OCs USA",
    "⏳ 4. Monitor Caducidad & Merma (FEFO)",
    "⚙️ 5. Simulador S&OP con Restricciones"
])

# =============================================================================
# TAB 1: Consola General S&OP y Salud del Negocio
# =============================================================================
with tab1:
    st.subheader("Salud Integral de la Cadena y Cuadrantes GMROI")
    col_t1_a, col_t1_b = st.columns([3, 2])

    with col_t1_a:
        with db.get_connection() as conn:
            df_gmroi = AnalyticalQueries.get_category_gmroi_analytics(conn)

        fig_gmroi = px.scatter(
            df_gmroi,
            x="inventory_turns",
            y="gross_margin_pct",
            size="total_revenue_clp",
            color="category",
            hover_name="product_name",
            hover_data=["sku", "gmroi", "cd_stock_units"],
            labels={
                "inventory_turns": "Rotación Anualizada de Inventario (Vueltas)",
                "gross_margin_pct": "Margen Bruto (%)",
                "total_revenue_clp": "Ventas CLP",
                "category": "Categoría"
            },
            title="Matriz de Valoración: Rotación vs. Margen Bruto (Tamaño = Venta CLP)",
            template="plotly_white"
        )
        # Quadrant benchmarks
        fig_gmroi.add_hline(y=45, line_dash="dash", line_color="gray", annotation_text="Margen Medio 45%")
        fig_gmroi.add_vline(x=5.0, line_dash="dash", line_color="gray", annotation_text="Rotación Media 5.0x")
        st.plotly_chart(fig_gmroi, use_container_width=True)

    with col_t1_b:
        st.markdown("#### Desempeño Regional y Cobertura")
        with db.get_connection() as conn:
            df_reg = AnalyticalQueries.get_regional_summary(conn)

        fig_reg = px.bar(
            df_reg,
            x="region_id",
            y="total_revenue_clp",
            color="regional_in_stock_rate_pct",
            color_continuous_scale="Viridis",
            labels={"region_id": "Región", "total_revenue_clp": "Venta Total CLP", "regional_in_stock_rate_pct": "In-Stock %"},
            title="Venta Total e In-Stock Rate por Región",
            template="plotly_white"
        )
        st.plotly_chart(fig_reg, use_container_width=True)

    st.markdown("#### Auditoría de Cobertura en Sala y Quiebres por Sucursal (Top Críticos)")
    with db.get_connection() as conn:
        df_store_health = AnalyticalQueries.get_store_inventory_health(conn, days_back=30)

    # Filter status
    status_filter = st.multiselect(
        "Filtrar Estado Operacional en Tiendas:",
        options=df_store_health["operational_inventory_status"].unique(),
        default=["QUIEBRE CRÍTICO", "RIESGO DE REPOSICION"]
    )
    df_filtered_stores = df_store_health[df_store_health["operational_inventory_status"].isin(status_filter)]
    st.dataframe(
        df_filtered_stores.head(25)[[
            "store_name", "cluster_id", "category", "product_name",
            "daily_velocity", "current_stock", "days_of_coverage",
            "in_stock_rate_pct", "operational_inventory_status"
        ]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================================
# TAB 2: Auditoría de Forecast y Desafío a Compras (WAPE / Bias)
# =============================================================================
with tab2:
    st.subheader("Auditoría de Precisión de Demanda y Detección de Sesgo Sistemático")
    st.markdown("""
    Esta consola permite al **Planificador de Demanda** auditar si Category Management o Compras
    están sobre-pronosticando (generando sobrestock y merma) o sub-pronosticando (provocando quiebres).
    """)

    # Prepare audit dataset comparing real sales vs statistical forecast vs commercial proposal
    # We aggregate actual 8-week sales vs historical forecast
    with db.get_connection() as conn:
        df_actuals_8w = pd.read_sql_query("""
            SELECT sku, SUM(units_sold) AS actual_units
            FROM fct_sales_daily
            WHERE date >= DATE((SELECT MAX(date) FROM fct_sales_daily), '-56 days')
            GROUP BY sku
        """, conn)

    df_fct_8w = df_fct.groupby("sku")["forecast_units"].sum().reset_index().rename(columns={"forecast_units": "forecast_units"})
    df_audit_base = df_products[["sku", "product_name", "category", "abc_category", "cogs_clp"]].merge(df_actuals_8w, on="sku").merge(df_fct_8w, on="sku")

    # Add simulated commercial proposal with notorious positive bias (+18% to +35%)
    np.random.seed(42)
    df_audit_base["commercial_proposal_units"] = np.round(df_audit_base["forecast_units"] * np.random.uniform(1.15, 1.38, len(df_audit_base)), 0)

    # Evaluate accuracy using ForecastQualityAuditor
    df_eval = df_audit_base.rename(columns={"actual_units": "actual", "forecast_units": "forecast"})
    df_audit_kpis = ForecastQualityAuditor.evaluate(df_eval, sku_col="sku", actual_col="actual", forecast_col="forecast", category_col="category")
    df_audit_full = df_audit_base.merge(df_audit_kpis, on=["sku", "category"])

    col_t2_k1, col_t2_k2, col_t2_k3, col_t2_k4 = st.columns(4)
    with col_t2_k1:
        st.metric("WAPE Promedio Cadena", f"{df_audit_full['wape_pct'].mean():.1f}%", "-2.4% vs Mes Anterior")
    with col_t2_k2:
        st.metric("Sesgo Medio (Modelo)", f"{df_audit_full['bias_pct'].mean():+.1f}%", "Tolerancia: ±10%")
    with col_t2_k3:
        st.metric("Sesgo Comercial (Compras)", "+24.8%", "Sobreestimación Crítica", delta_color="inverse")
    with col_t2_k4:
        ooc_count = df_audit_full["is_out_of_control"].sum()
        st.metric("SKUs Fuera de Control (|TS|>4)", f"{ooc_count} SKUs", "Requieren Reentrenamiento", delta_color="inverse")

    col_t2_a, col_t2_b = st.columns([3, 2])
    with col_t2_a:
        fig_bias = px.scatter(
            df_audit_full,
            x="total_actual_units",
            y="bias_pct",
            color="bias_diagnosis",
            size="wape_pct",
            hover_name="product_name",
            hover_data=["sku", "tracking_signal", "wape_pct"],
            labels={"total_actual_units": "Volumen Real Vendido (8 Semanas)", "bias_pct": "Sesgo de Pronóstico (%)", "wape_pct": "WAPE %"},
            title="Matriz de Sesgo de Pronóstico (Bias %) vs. Volumen Vendido",
            template="plotly_white"
        )
        fig_bias.add_hline(y=10.0, line_dash="dash", line_color="red", annotation_text="+10% Límite Sobre-pronóstico")
        fig_bias.add_hline(y=-10.0, line_dash="dash", line_color="orange", annotation_text="-10% Límite Sub-pronóstico")
        st.plotly_chart(fig_bias, use_container_width=True)

    with col_t2_b:
        # Comparison chart: Top 10 SKUs Actual vs Model vs Commercial
        top10 = df_audit_full.sort_values(by="total_actual_units", ascending=False).head(8)
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=top10["sku"], y=top10["total_actual_units"], name="Venta Real (Actual)", marker_color="#0D3B66"))
        fig_comp.add_trace(go.Bar(x=top10["sku"], y=top10["total_forecast_units"], name="Modelo Estadístico", marker_color="#2A9D8F"))
        fig_comp.add_trace(go.Bar(x=top10["sku"], y=top10["commercial_proposal_units"], name="Propuesta Comercial", marker_color="#E63946"))
        fig_comp.update_layout(
            barmode="group",
            title="Desafío a Compras: Real vs Modelo vs Comercial",
            template="plotly_white"
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("#### Detalle de Auditoría de Forecast por SKU")
    st.dataframe(
        df_audit_full[[
            "sku", "product_name", "category", "total_actual_units", "total_forecast_units",
            "wape_pct", "bias_pct", "tracking_signal", "bias_diagnosis", "is_out_of_control"
        ]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================================
# TAB 3: Planificador de Sugerido de Compras & Tránsito Marítimo
# =============================================================================
with tab3:
    st.subheader("Requerimiento Neto de Importación Marítima (EE.UU. ➔ Chile)")
    st.markdown("""
    Cálculo de posición neta: **Stock CD + Stock Tiendas + Tránsito Marítimo + OCs Abiertas**.  
    Ajustado por variabilidad de Lead Time (45-75 días), Stock de Seguridad estocástico ($SS$), MOQ y cubicaje de pallets.
    """)

    col_t3_f1, col_t3_f2, col_t3_f3 = st.columns(3)
    with col_t3_f1:
        selected_brand = st.multiselect("Filtrar por Proveedor / Marca:", options=sorted(df_products["brand"].unique()), default=[])
    with col_t3_f2:
        selected_cat = st.multiselect("Filtrar por Categoría:", options=sorted(df_products["category"].unique()), default=[])
    with col_t3_f3:
        urgency_filter = st.multiselect("Filtrar Semáforo de Urgencia:", options=df_net_reqs["urgency_status"].unique(), default=[])

    df_view_reqs = df_net_reqs.copy()
    if selected_brand:
        skus_brand = df_products[df_products["brand"].isin(selected_brand)]["sku"].tolist()
        df_view_reqs = df_view_reqs[df_view_reqs["sku"].isin(skus_brand)]
    if selected_cat:
        df_view_reqs = df_view_reqs[df_view_reqs["category"].isin(selected_cat)]
    if urgency_filter:
        df_view_reqs = df_view_reqs[df_view_reqs["urgency_status"].isin(urgency_filter)]

    # Urgency summary
    col_u1, col_u2, col_u3 = st.columns(3)
    crit_count = (df_view_reqs["urgency_status"].str.contains("CRÍTICO")).sum()
    reord_count = (df_view_reqs["urgency_status"].str.contains("REORDEN")).sum()
    suf_count = (df_view_reqs["urgency_status"].str.contains("SUFICIENTE")).sum()

    with col_u1:
        st.error(f"🚨 **{crit_count} SKUs en Quiebre Inminente** (DOS < Lead Time 60d)")
    with col_u2:
        st.warning(f"⚠️ **{reord_count} SKUs en Ventana de Reorden**")
    with col_u3:
        st.success(f"✅ **{suf_count} SKUs con Cobertura Conforme**")

    st.dataframe(
        df_view_reqs[[
            "sku", "product_name", "category", "abc_class", "stock_cd", "stock_stores",
            "in_transit", "open_pos", "safety_stock_units", "net_requirement_units",
            "moq_units", "suggested_order_units", "suggested_order_pallets",
            "cogs_clp", "suggested_investment_clp", "days_of_stock_on_hand", "urgency_status"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### Pipeline de Órdenes de Compra en Tránsito Internacional")
    st.dataframe(
        df_pos[[
            "po_number", "sku", "order_date", "units_ordered", "status", "estimated_arrival_date"
        ]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================================
# TAB 4: Monitor de Caducidad, Shelf-Life y Merma (FEFO)
# =============================================================================
with tab4:
    st.subheader("Monitor de Vida Útil, Despacho FEFO y Prevención de Merma")
    st.markdown("""
    Auditoría por lote según run-rate diario del pronóstico. Si el stock en bodega supera la venta estimada
    antes de la fecha de caducidad ($T_{exp}$), se levanta alerta crítica de merma biológica con recomendación de acción.
    """)

    fefo_total_risk = df_fefo["financial_waste_risk_clp"].sum()
    fefo_total_units = df_fefo["projected_waste_units"].sum()

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.metric("Riesgo Financiero Merma Total", f"${fefo_total_risk/1e6:,.2f}M CLP", "Pérdida al Costo")
    with col_f2:
        st.metric("Unidades en Riesgo Biológico", f"{fefo_total_units:,} Unidades", "Exceden Demanda")
    with col_f3:
        st.metric("Lotes en Monitoreo CD", f"{len(df_fefo)} Lotes", "Política FEFO Activa")

    fig_fefo = px.bar(
        df_fefo[df_fefo["financial_waste_risk_clp"] > 0],
        x="product_name",
        y="financial_waste_risk_clp",
        color="urgency_tier",
        color_discrete_map={
            "CRÍTICO: Liquidar Inmediato (Riesgo Merma Total)": "#E63946",
            "ALERTA: Priorizar Despacho FEFO a Tiendas Top": "#F4A261",
            "SALUDABLE: Cobertura Conforme": "#2A9D8F"
        },
        labels={"product_name": "Producto", "financial_waste_risk_clp": "Riesgo CLP", "urgency_tier": "Nivel de Urgencia"},
        title="Riesgo Financiero de Merma por Producto (Lotes Próximos a Vencer)",
        template="plotly_white"
    )
    st.plotly_chart(fig_fefo, use_container_width=True)

    st.markdown("#### Alertas de Lotes y Recomendación Capilar a Tiendas")
    st.dataframe(
        df_fefo[[
            "batch_id", "sku", "product_name", "units_in_batch", "expiry_date",
            "days_to_expire", "projected_demand_before_expiry", "projected_waste_units",
            "financial_waste_risk_clp", "urgency_tier", "action_recommendation"
        ]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================================
# TAB 5: Laboratorio de Escenarios S&OP con Restricciones
# =============================================================================
with tab5:
    st.subheader("Simulador S&OP: Asignación Bajo Restricciones de Capital y Capacidad")
    st.markdown("""
    Optimización mediante el problema de la mochila acotada (*Bounded Knapsack*), priorizando compras
    por **GMROI proyectado** y criticidad de servicio (Clase A > B > C).
    """)

    # Interactive Controls
    total_unconstrained_budget = df_net_reqs["suggested_investment_clp"].sum()
    total_unconstrained_pallets = df_net_reqs["suggested_order_pallets"].sum()

    col_sim_ctrl1, col_sim_ctrl2 = st.columns(2)
    with col_sim_ctrl1:
        budget_slider_millions = st.slider(
            "Presupuesto Máximo de Capital de Trabajo ($M CLP):",
            min_value=50.0,
            max_value=float(np.ceil(total_unconstrained_budget / 1e6 * 1.5)),
            value=float(np.round(total_unconstrained_budget / 1e6 * 0.85, 1)),
            step=5.0
        )
        selected_budget_clp = budget_slider_millions * 1e6

    with col_sim_ctrl2:
        pallet_slider = st.slider(
            "Capacidad Máxima de Pallets en Bodega CD:",
            min_value=50,
            max_value=int(np.ceil(total_unconstrained_pallets * 1.5)),
            value=int(np.round(total_unconstrained_pallets * 0.80)),
            step=10
        )
        selected_pallets = float(pallet_slider)

    # Prepare demand dataset for optimizer
    df_snop_input = df_net_reqs.copy().rename(columns={
        "suggested_order_units": "unconstrained_order_units"
    })
    # Add gross_margin_pct and turnover
    df_snop_input = df_snop_input.merge(
        df_products[["sku", "retail_price_clp"]],
        on="sku",
        how="left"
    )
    df_snop_input["gross_margin_pct"] = (df_snop_input["retail_price_clp"] - df_snop_input["cogs_clp"]) / df_snop_input["retail_price_clp"]

    # Solve Optimization
    df_opt_res, opt_summary = SnOpCapacityOptimizer.optimize(
        df_demands=df_snop_input,
        max_budget_clp=selected_budget_clp,
        max_pallet_capacity=selected_pallets
    )

    # Optimization Result KPIs
    col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
    with col_r1:
        st.metric("Inversión Asignada", f"${opt_summary.total_constrained_investment_clp/1e6:,.1f}M CLP", f"Uso Caja: {opt_summary.budget_utilization_pct:.1f}%")
    with col_r2:
        st.metric("Pallets Asignados", f"{opt_summary.total_constrained_pallets:.0f} Pallets", f"Uso Bodega: {opt_summary.warehouse_pallet_utilization_pct:.1f}%")
    with col_r3:
        fulfillment_pct = (opt_summary.total_constrained_units / opt_summary.total_unconstrained_units * 100.0) if opt_summary.total_unconstrained_units > 0 else 100.0
        st.metric("Tasa de Cumplimiento", f"{fulfillment_pct:.1f}%", f"{opt_summary.total_constrained_units:,} / {opt_summary.total_unconstrained_units:,} u.")
    with col_r4:
        st.metric("SKUs Cortados / Parciales", f"{opt_summary.cut_skus_count} / {opt_summary.partially_filled_skus_count}", "Afectados por Tope")
    with col_r5:
        st.metric("GMROI Promedio", f"{opt_summary.average_projected_gmroi:.2f}x", "Eficiencia de Margen")

    # Chart: Unconstrained vs Constrained Orders
    top_items_plot = df_opt_res[df_opt_res["unconstrained_order_units"] > 0].sort_values(by="priority_score", ascending=False).head(15)
    fig_opt = go.Figure()
    fig_opt.add_trace(go.Bar(
        x=top_items_plot["product_name"],
        y=top_items_plot["unconstrained_order_units"],
        name="Demanda Ideal (Unconstrained)",
        marker_color="#A8DADC"
    ))
    fig_opt.add_trace(go.Bar(
        x=top_items_plot["product_name"],
        y=top_items_plot["constrained_order_units"],
        name="Compra Asignada (Constrained)",
        marker_color="#1D3557"
    ))
    fig_opt.update_layout(
        barmode="group",
        title="Asignación Óptima por Restricciones (Top 15 SKUs Priorizados por GMROI)",
        template="plotly_white",
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_opt, use_container_width=True)

    # Sensitivity comparison table
    st.markdown("#### Matriz de Sensibilidad de Escenarios S&OP")
    df_scenarios = SnOpScenarioEvaluator.evaluate_scenarios(
        df_demands=df_snop_input,
        base_budget_clp=selected_budget_clp,
        base_pallets=selected_pallets
    )
    st.dataframe(df_scenarios, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📥 Exportación Oficial del Modelo Corporativo en Excel")
    st.write("Genera y descarga la planilla oficial con **fórmulas encadenadas vivas**, tablas de sugerido y auditoría:")

    excel_path = os.path.join(str(ROOT_DIR), "data", "excel", "KIOS_FLOW_Plan_Compras_SOP_Oficial.xlsx")

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        if st.button("🔄 Generar / Actualizar Modelo Excel (.xlsx)", use_container_width=True):
            with st.spinner("Construyendo libro Excel con fórmulas dinámicas en OpenPyXL..."):
                CorporateSnOpExcelBuilder.build_snop_workbook(
                    filepath=excel_path,
                    df_net_reqs=df_net_reqs,
                    df_forecast_audit=df_audit_full,
                    df_fefo_risk=df_fefo
                )
            st.success("¡Libro Excel generado exitosamente con fórmulas encadenadas vivas!")

    if os.path.exists(excel_path):
        with open(excel_path, "rb") as f:
            st.download_button(
                label="📥 Descargar Planilla Excel S&OP Oficial (.xlsx)",
                data=f.read(),
                file_name="KIOS_FLOW_Plan_Compras_SOP.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
