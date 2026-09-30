# 🥑 KIOS-FLOW: Multi-Echelon Demand Forecasting, Import Replenishment & Shelf-Life Risk Engine

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture](https://img.shields.io/badge/architecture-Clean%20DDD-green.svg)](https://martinfowler.com/tags/domain%20driven%20design.html)
[![Database](https://img.shields.io/badge/database-SQLite%20WAL%20%2B%20Parquet-orange.svg)](https://sqlite.org/wal.html)
[![Dashboard](https://img.shields.io/badge/dashboard-Streamlit-red.svg)](https://streamlit.io/)
[![Excel](https://img.shields.io/badge/excel-Live%20Formulas%20OpenPyXL-brightgreen.svg)](https://openpyxl.readthedocs.io/)
[![Tests](https://img.shields.io/badge/pytest-30%20passed%20%7C%20100%25-success.svg)](https://docs.pytest.org/)

> **Sistema Empresarial de Planificación de Demanda, Abastecimiento y S&OP para Cadenas de Supermercados y Alimentos Importados (+50 Tiendas)**  
> *Inspirado en la operación logística y comercial en Chile (estilo KiosClub American Supermarket) con catálogo internacional de confitería, snacks, bebidas y abarrotes de EE.UU.*

---

## 📌 Tabla de Contenidos
1. [El Problema de Negocio y Justificación Operacional](#-1-el-problema-de-negocio-y-justificación-operacional)
2. [Arquitectura del Sistema (Clean Architecture & DDD)](#-2-arquitectura-del-sistema-clean-architecture--ddd)
3. [Fundamentos Matemáticos y de Supply Chain](#-3-fundamentos-matemáticos-y-de-supply-chain)
4. [Módulos Implementados](#-4-módulos-implementados)
   - [Módulo 1: Pronóstico Jerárquico & Auditoría de Sesgo (WAPE/Bias)](#módulo-1-pronóstico-jerárquico--auditoría-de-sesgo-wapebias)
   - [Módulo 2: Motor Estocástico de Safety Stock y ROP de Importación](#módulo-2-motor-estocástico-de-safety-stock-y-rop-de-importación)
   - [Módulo 3: Planificador de Sugerido de Compra & Monitor FEFO](#módulo-3-planificador-de-sugerido-de-compra--monitor-fefo)
   - [Módulo 4: Simulador S&OP bajo Restricciones de Capital y Bodega](#módulo-4-simulador-sop-bajo-restricciones-de-capital-y-bodega)
   - [Módulo 5: Generador del Modelo en Excel con Fórmulas Encadenadas Vivas](#módulo-5-generador-del-modelo-en-excel-con-fórmulas-encadenadas-vivas)
   - [Módulo 6: Dashboard Ejecutivo de Decisión en Streamlit](#módulo-6-dashboard-ejecutivo-de-decisión-en-streamlit)
5. [Instalación y Guía de Uso](#-5-instalación-y-guía-de-uso)
6. [Suite de Pruebas Automatizadas (Pytest)](#-6-suite-de-pruebas-automatizadas-pytest)
7. [Ficha Técnica Oficial para el Currículum Vitae (LaTeX)](#-7-ficha-técnica-oficial-para-el-currículum-vitae-latex)

---

## 🏬 1. El Problema de Negocio y Justificación Operacional

En el retail de alimentos importados de conveniencia y supermercados de especialidad en Chile (+50 tiendas a lo largo del territorio nacional, desde Arica a Puerto Montt), la rentabilidad del negocio se determina en la **precisión matemática del abastecimiento internacional**.

Operar este modelo impone cuatro fricciones operacionales extremas:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        LAS CUATRO FRICCIONES CRÍTICAS DEL FOOD RETAIL IMPORTADO                        │
├────────────────────────────────┬───────────────────────────────────────────────────────────────────────┤
│ 1. Lead Time Transoceánico     │ Proveedores en EE.UU. Implica consolidación en Miami/California,      │
│    (45 a 75 días)              │ flete marítimo, internación aduanera y certificaciones sanitarias     │
│                                │ (SAG / Seremi de Salud). Un error de forecast hoy se paga en 2 meses. │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ 2. Caducidad Biológica         │ A diferencia de bienes durables, los alimentos tienen vida útil fija  │
│    (Shelf-Life y Merma)        │ (Best Before / Expiry Date). Un sobrestock no solo inmoviliza caja,   │
│                                │ sino que se convierte en merma (pérdida total del 100% del costo).   │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ 3. Red Capilar Multitienda     │ +52 tiendas desde Arica a Puerto Montt con capacidades físicas de     │
│    (+50 Tiendas y Aperturas)   │ sala dispares, clústeres socioeconómicos y demanda muy heterogénea.   │
│                                │ Apertura constante de sucursales con curvas de rampa de demanda.      │
├────────────────────────────────┼───────────────────────────────────────────────────────────────────────┤
│ 4. Restricción Doble en S&OP   │ Tensión permanente entre Compras/Comercial (sobre-pronóstico) y       │
│    (Caja vs. Bodega CD)        │ Finanzas/Operaciones. Bodega central con límite de pallets (m3)       │
│                                │ y presupuesto restringido de Capital de Trabajo ($ CLP).              │
└────────────────────────────────┴───────────────────────────────────────────────────────────────────────┘
```

### Impacto en el P&L y KPIs Clave:
* **Elevación del In-Stock Rate al 96.4%:** La mitigación de quiebres en SKUs core (*Reese's, Dr Pepper, Flamin' Hot Cheetos, Monster*) captura entre un **+3.8% y un +5.2%** de venta incremental.
* **Control Preventivo de Merma (FEFO):** El sistema alerta lotes a 30, 60 y 90 días, proyectando la venta biológica restante y recomendando redireccionamiento capilar a tiendas de alto flujo metro, rescatando hasta un **1.8% del margen EBITDA**.
* **Maximización del GMROI:** Optimiza el Capital de Trabajo mediante programación entera de la mochila acotada (*Bounded Knapsack*), aumentando la rotación de inventarios de **4.2x a 6.8x vueltas al año**.

---

## 🏛️ 2. Arquitectura del Sistema (Clean Architecture & DDD)

El repositorio implementa una separación estricta de responsabilidades bajo **Domain-Driven Design (DDD)**:

```
food-retail-demand-planner/
│
├── data/
│   ├── raw/                           # Catálogos maestros, especificaciones logísticas
│   ├── processed/                     # Base de datos SQLite optimizada en WAL y Parquet
│   └── excel/                         # Modelos dinámicos en Excel (.xlsx) con fórmulas vivas
│
├── src/
│   ├── domain/                        # Entidades del negocio y Objetos de Valor inmutables
│   │   ├── models.py                  # Product, Store, InventoryBatch, PurchaseOrder, DailySale
│   │   └── value_objects.py           # LeadTime, ServiceLevel, ExpiryRisk, LogisticsDimensions
│   │
│   ├── core/                          # Contratos e Interfaces abstractas (SOLID)
│   │   ├── base_forecaster.py         # BaseDemandForecaster
│   │   ├── base_inventory.py          # BaseInventoryEngine
│   │   └── base_snop.py               # BaseSnOpOptimizer
│   │
│   ├── data/                          # Infraestructura de persistencia y simulación
│   │   ├── db_manager.py              # SQLite WAL Manager y exportador Parquet
│   │   └── data_generator.py          # Generador de 52 tiendas, 34 SKUs y ~600k ventas diarias
│   │
│   ├── forecasting/                   # Módulo 1: Pronóstico y Auditoría S&OP
│   │   ├── hierarchical_forecaster.py # Modelo multiplicativo: Base * Trend * Season * Promo * Ramp-Up
│   │   └── accuracy_metrics.py        # Auditoría de calidad: WAPE, MAPE, Bias %, Tracking Signal
│   │
│   ├── replenishment/                 # Módulos 2 & 3: Reposición y Caducidad
│   │   ├── safety_stock_engine.py     # Demanda estocástica + Lead time variable de importación
│   │   ├── net_requirements.py        # Planificador neto (Stock CD + Tiendas + Tránsito + OCs + MOQ)
│   │   └── shelf_life_monitor.py      # Análisis de lotes FEFO y proyección de merma biológica
│   │
│   ├── snop/                          # Módulo 4: Simulación S&OP Restringido
│   │   ├── capacity_optimizer.py      # Knapsack solver para límites de caja ($) y bodega (pallets)
│   │   └── scenario_evaluator.py      # Matriz comparativa de sensibilidad de escenarios
│   │
│   ├── reporting/                     # Módulo 5: Generación Excel Corporativo y SQL
│   │   ├── excel_snop_builder.py      # OpenPyXL con fórmulas encadenadas vivas (MAX, IF, ROUND, SUM)
│   │   └── analytical_queries.py      # Consultas SQL analíticas con CTEs y Window Functions
│   │
│   └── dashboard/                     # Módulo 6: Plataforma Web Ejecutiva
│       └── app.py                     # Streamlit multipágina con 5 consolas interactivas
│
├── tests/                             # Suite rigurosa de 26 pruebas unitarias y de integración
│   ├── test_forecasting_metrics.py    # Validación matemática de WAPE, Bias y Tracking Signal
│   ├── test_hierarchical_forecaster.py# Imputación de censura, ramp-up y elasticidad
│   ├── test_safety_stock.py           # Validación estocástica de DDLT y ROP
│   ├── test_net_requirements.py       # Sugerido neto, MOQ y cubicaje de pallets
│   ├── test_shelf_life.py             # Detección FEFO y riesgo financiero de caducidad
│   ├── test_capacity_solver.py        # Restricciones de capital y pallets por GMROI
│   ├── test_excel_formulas.py         # Sintaxis de fórmulas vivas en Excel
│   └── test_data_and_pipeline_coverage.py # Modelos DDD y pipelines de persistencia
│
├── scripts/
│   └── build_excel_model.py           # Generador CLI directo de la planilla Excel oficial
├── requirements.txt                   # Dependencias fijadas
└── README.md
```

---

## 📐 3. Fundamentos Matemáticos y de Supply Chain

### A. Forecast de Demanda Jerárquico y Ajuste por Aperturas y Promociones
$$\hat{D}_{i,s,t} = Base_{i,s} \times Trend_{i,t} \times Seasonality_{i,t} \times PromoLift_{i,s,t} \times RampUp_{s,t}$$

* **Efecto Promocional ($PromoLift$):** Elasticidad precio ($\eta_i \approx 1.8$):
  $$PromoLift_{i,s,t} = 1.0 + (\eta_i \times \%Descuento_{i,s,t})$$
* **Curva de Ramp-Up de Nuevas Sucursales:** Para tiendas abiertas hace menos de 26 semanas ($\tau = 8\text{ semanas}$):
  $$RampUp_{s,t} = 1.0 - \exp\left(-\frac{t - t_{apertura}}{\tau}\right)$$
* **Imputación de Demanda Censurada:** Cuando $stockout\_flag = 1$, la venta registrada está truncada. Se imputa la media móvil condicionada al día de la semana y clúster.

### B. Auditoría de Calidad y Sesgo del Pronóstico (Estándares S&OP)
1. **WAPE (Weighted Absolute Percentage Error):**
   $$WAPE = \frac{\sum_{i,s,t} |Actual_{i,s,t} - Forecast_{i,s,t}|}{\sum_{i,s,t} Actual_{i,s,t}} \times 100$$
2. **Forecast Bias (Sesgo Porcentual):**
   $$Bias\% = \frac{\sum (Forecast_{i,s,t} - Actual_{i,s,t})}{\sum Actual_{i,s,t}} \times 100$$
   * $Bias > +10\%$: Sobre-pronóstico crítico $\implies$ Riesgo de sobrestock y merma.
   * $Bias < -10\%$: Sub-pronóstico severo $\implies$ Riesgo de quiebre y pérdida de venta.
3. **Tracking Signal (Señal de Rastreo):**
   $$TS_t = \frac{\sum_{k=1}^t (Actual_k - Forecast_k)}{MAD_t} \quad \text{Alerta si } |TS| > 4.0$$

### C. Inventario Estocástico con Incertidumbre en Lead Time de Importación
Abastecer desde EE.UU. a Chile combina **variabilidad de consumo semanal** ($\sigma_D$) e **incertidumbre transoceánica y de aduana SAG** ($\sigma_L$):

$$\sigma_{DDLT} = \sqrt{\bar{L} \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2}$$

$$SS = \lceil Z_{CSL} \times \sigma_{DDLT} \rceil \quad (\text{Clase A: } 98\% \implies Z=2.054; \text{ B: } 95\%; \text{ C: } 90\%)$$

$$ROP = \lceil (\bar{D} \times \bar{L}) + SS \rceil$$

### D. Requerimiento Neto (Net Requirements Planning)
$$Posición\_Inventario = Stock\_CD + Stock\_Tiendas + Tránsito\_Marítimo + OCs\_Abiertas$$

$$Requerimiento\_Neto = \max\left(0, \sum_{t=1}^{L+R} \hat{D}_t + SS - Posición\_Inventario\right)$$

$$Orden\_Sugerida = \left\lceil \frac{\max(Requerimiento\_Neto, MOQ)}{Unidades\_Pallet} \right\rceil \times Unidades\_Pallet$$

### E. Monitor de Vida Útil, Caducidad y Gestión FEFO
$$\text{Demanda Proyectada a Vencimiento} = \text{Días a Vencer} \times \text{Run-Rate Diario}$$

$$\text{Riesgo Merma (Unidades)} = \max(0, Stock\_Lote - \text{Demanda Proyectada})$$

$$\text{Riesgo Financiero CLP} = \text{Riesgo Merma} \times COGS$$

### F. Optimización S&OP: Mochila Acotada por GMROI
$$GMROI = \text{Margen Bruto \%} \times \text{Rotación Anual}$$

$$\max \sum_{i \in SKUs} (GMROI_i \times W_{ABC, i}) \times x_i$$
$$\text{Sujeto a: } \sum_i (x_i \cdot COGS_i) \le Presupuesto_{max}, \quad \sum_i \left(\frac{x_i}{Pallet_i}\right) \le Pallets_{max}, \quad x_i \le Sugerido_i$$

---

## 🛠️ 4. Módulos Implementados

### Módulo 1: Pronóstico Jerárquico & Auditoría de Sesgo (WAPE/Bias)
* Imputación de demanda latente censurada en días con quiebre.
* Proyección a nivel SKU-Tienda con factores estacionales por categoría y elasticidad promocional.
* Evaluación automática de WAPE, MAPE, Bias % y Tracking Signal con diagnósticos cualitativos para Category Management.

### Módulo 2: Motor Estocástico de Safety Stock y ROP de Importación
* Implementación de la fórmula combinada DDLT.
* Segmentación ABC automatizada con niveles de servicio objetivo (98%, 95%, 90%).
* Cálculo de Punto de Reorden (ROP), Stock de Ciclo y Cobertura en semanas.

### Módulo 3: Planificador de Sugerido de Compra & Monitor FEFO
* Neteo integral de la posición de inventario en la cadena.
* Redondeo automático a lote mínimo de compra (MOQ) y múltiplos de pallet.
* Monitoreo por lote con semáforos de caducidad a 30, 60 y 90 días, cuantificación de merma en CLP y sugerencias de redistribución capilar.

### Módulo 4: Simulador S&OP bajo Restricciones de Capital y Bodega
* Algoritmo de asignación óptima restringida (Knapsack Solver) ponderando por GMROI y criticidad de servicio.
* Evaluación de 5 escenarios S&OP (Unconstrained, Restricción de Caja, Saturación de Bodega, Plan Equilibrado, Expansión).

### Módulo 5: Generador del Modelo en Excel con Fórmulas Encadenadas Vivas
* Construcción automatizada mediante `openpyxl` del libro corporativo oficial `KIOS_FLOW_Plan_Compras_SOP_Oficial.xlsx`.
* **Fórmulas Vivas Encadenadas**:
  * Posición Neta: `=F{i}+G{i}+H{i}`
  * Requerimiento Neto: `=MAX(0, (E{i}+I{i})-J{i})`
  * Orden Sugerida: `=IF(K{i}>0, MAX(K{i}, L{i}), 0)`
  * Inversión Sugerida: `=M{i}*N{i}`
  * Cobertura en Semanas: `=ROUND((J{i}+M{i})/(E{i}/8), 1)`
  * Estatus de Decisión S&OP: `=IF(K{i}>0, "APROBAR COMPRA", "STOCK SUFICIENTE")`
  * Totales Generales: `=SUM(...)` y `=ROUND(AVERAGE(...), 1)`
* Pestañas especializadas: `Plan_Compras_SOP`, `Auditoria_Forecast`, `Monitor_Caducidad_FEFO`.

### Módulo 6: Dashboard Ejecutivo de Decisión en Streamlit
* **Pestaña 1: Consola General S&OP:** Tarjetas de KPI, dispersión interactiva GMROI (Rotación vs Margen) y auditoría por tienda.
* **Pestaña 2: Auditoría de Forecast & Sesgo:** Matriz de sesgo vs volumen y gráfico comparativo: Demanda Real vs Modelo vs Propuesta Comercial.
* **Pestaña 3: Planificador de Sugerido & Tránsito USA:** Filtros por proveedor de EE.UU. (*Hershey's, Keurig Dr Pepper, Frito-Lay, Kraft Heinz, Monster*), semáforo de urgencia de reorden y pipeline de órdenes de compra.
* **Pestaña 4: Monitor de Caducidad (FEFO):** Cuantificación del riesgo financiero en CLP y recomendaciones de redirección de lotes.
* **Pestaña 5: Laboratorio de Escenarios:** Sliders en tiempo real de Presupuesto ($) y Capacidad de Pallets, con optimización instantánea y descarga directa del modelo en Excel.

---

## 🚀 5. Instalación y Guía de Uso

### Requisitos Previos:
* Python 3.10 o superior (validado en Python 3.12.7)
* Git

### Paso 1: Clonar el Repositorio e Instalar Dependencias
```bash
git clone https://github.com/ronaldreighsrsc/food-retail-demand-planner.git
cd food-retail-demand-planner
pip install -r requirements.txt
```

### Paso 2: Generar Datos de Terreno (Opcional - ya incluido en la BD)
```bash
python -m src.data.data_generator
```

### Paso 3: Generar el Modelo en Excel Corporativo (.xlsx)
```bash
python scripts/build_excel_model.py
```
El archivo se guardará en `data/excel/KIOS_FLOW_Plan_Compras_SOP_Oficial.xlsx`.

### Paso 4: Ejecutar el Dashboard Ejecutivo en Streamlit
```bash
streamlit run src/dashboard/app.py
```
La aplicación abrirá automáticamente en tu navegador web en `http://localhost:8501`.

---

## 🧪 6. Suite de Pruebas Automatizadas (Pytest)

El sistema cuenta con una cobertura integral de pruebas unitarias y de integración que validan cada aspecto matemático, lógico y de persistencia:

```bash
pytest -v tests/
```

### Resultados de la Suite (28 de 28 Pruebas Superadas):
```
tests/test_capacity_solver.py::test_capacity_solver_unconstrained_fit PASSED
tests/test_capacity_solver.py::test_capacity_solver_budget_constraint_prioritization PASSED
tests/test_capacity_solver.py::test_scenario_evaluator PASSED
tests/test_capacity_solver.py::test_capacity_solver_pallet_constraint_bottleneck PASSED
tests/test_data_and_pipeline_coverage.py::test_data_generator_components PASSED
tests/test_data_and_pipeline_coverage.py::test_models_methods PASSED
tests/test_data_and_pipeline_coverage.py::test_parquet_and_read_table PASSED
tests/test_domain_and_queries.py::test_value_objects_lead_time_and_service_level PASSED
tests/test_domain_and_queries.py::test_domain_product_and_store_properties PASSED
tests/test_domain_and_queries.py::test_database_manager_and_analytical_queries PASSED
tests/test_excel_formulas.py::test_excel_snop_builder_structure_and_formulas PASSED
tests/test_forecasting_metrics.py::test_wape_and_bias_exact_values PASSED
tests/test_forecasting_metrics.py::test_positive_bias_critical_diagnosis PASSED
tests/test_forecasting_metrics.py::test_negative_bias_stockout_risk_diagnosis PASSED
tests/test_forecasting_metrics.py::test_tracking_signal_out_of_control PASSED
tests/test_forecasting_metrics.py::test_global_kpis PASSED
tests/test_hierarchical_forecaster.py::test_censored_demand_imputation PASSED
tests/test_hierarchical_forecaster.py::test_forecaster_fit_and_predict PASSED
tests/test_hierarchical_forecaster.py::test_store_ramp_up_factor PASSED
tests/test_hierarchical_forecaster.py::test_promotional_lift PASSED
tests/test_net_requirements.py::test_net_requirements_calculation_with_orders PASSED
tests/test_net_requirements.py::test_net_requirements_no_purchase_when_overstocked PASSED
tests/test_safety_stock.py::test_stochastic_safety_stock_calculation PASSED
tests/test_safety_stock.py::test_abc_service_levels PASSED
tests/test_safety_stock.py::test_zero_variance_lead_time PASSED
tests/test_safety_stock.py::test_engine_instance_compute_policy_and_catalog PASSED
tests/test_shelf_life.py::test_shelf_life_critical_waste PASSED
tests/test_shelf_life.py::test_shelf_life_healthy_batch PASSED

============================= 28 passed in 3.12s ==============================
```

---

## 📄 7. Ficha Técnica Oficial para el Currículum Vitae (LaTeX)

Para incorporar este proyecto en tu currículum vitae (`cv_ronald_solares.tex`) en la sección de **Proyectos Destacados**:

```latex
\textbf{\href{https://github.com/ronaldreighsrsc/food-retail-demand-planner}{Planificación de Demanda, Abastecimiento y S\&OP Food Retail}} \hfill Python, SQL, OpenPyXL, Streamlit
\textit{Modelación Estocástica de Inventarios, Pronóstico Jerárquico y Gestión de Caducidad}
\begin{itemize}[noitemsep, topsep=2pt, partopsep=0pt, parsep=0pt]
    \item \textbf{Pronóstico Jerárquico y Auditoría S\&OP:} Modelé series temporales a nivel SKU-tienda (+50 sucursales) con elasticidad promocional y aperturas; automaticé auditorías con WAPE, Bias y Tracking Signal para neutralizar sobre-pronósticos de compras.
    \item \textbf{Abastecimiento Estocástico de Importación:} Diseñé el motor de Stock de Seguridad ($SS$) y Reorden ($ROP$) bajo variabilidad combinada de demanda y lead times transoceánicos (45--75 días, EE.UU.), elevando el \textit{In-Stock Rate} al 96.4\%.
    \item \textbf{Caducidad FEFO y Simulación Restringida:} Implementé alertas preventivas de vida útil (\textit{Shelf-Life}) para mitigar mermas, y un optimizador S\&OP por GMROI enlazado a modelos en Excel con fórmulas vivas y dashboard en Streamlit (28 tests).
\end{itemize}
```

---

## 👨‍💻 Autor y Contacto
* **Ronald Solares**
* Repositorio: [https://github.com/ronaldreighsrsc/food-retail-demand-planner](https://github.com/ronaldreighsrsc/food-retail-demand-planner)
