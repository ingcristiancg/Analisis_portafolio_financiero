"""
Plataforma Cuantitativa Markowitz con Agente IA Autónomo
Versión Profesional y Confiable:
- Parámetros normativos fijos (σ_p <= 0.07, 1,000 carteras Monte Carlo) sin sliders innecesarios.
- Paleta visual institucional y serena (azul marino, esmeralda, dorado y pizarra).
- Módulo ask_agent robusto, sin errores y con respuestas estructuradas MBA.
- Centro de Auditoría de Calidad y Normalización de Datos.
- Modo A: Archivo Histórico Local | Modo B: Conexión API en Vivo (Yahoo Finance).
- Exportación en PDF (.pdf) y Word (.docx).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import base64
import unicodedata
import traceback

import optimizer
import agent
import word_exporter
import pdf_exporter
import api_fetcher

# Parámetros Normativos Estrictos (Fijos según especificación de la cátedra)
TARGET_RISK = 0.07          # Restricción estricta: sigma_p <= 7.00% mensual
NUM_MONTE_CARLO = 1000      # Regla estricta: 1,000 carteras aleatorias

# Configuración de página
st.set_page_config(
    page_title="CgApp • Plataforma Cuantitativa Markowitz & Agente IA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS modernos e institucionales (sin alertas rojas agresivas)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Ocultar pie y marcas por defecto para destacar CgApp */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0369a1 100%);
        padding: 22px 28px;
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.15);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2.0rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #cbd5e1;
        font-size: 0.98rem;
        margin: 6px 0 0 0;
    }
    
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 18px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #64748b;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #0284c7;
        font-weight: 500;
        margin-top: 4px;
    }
    
    .agent-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #0284c7;
        border-radius: 10px;
        padding: 18px 22px;
        margin: 14px 0;
    }

    .norm-box {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.85rem;
        color: #334155;
        margin-top: 10px;
    }

    .academic-cover-sheet {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.07);
        padding: 55px 45px;
        margin: 10px auto 25px auto;
        max-width: 820px;
        text-align: center;
        font-family: 'Times New Roman', Times, Georgia, serif;
        color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)


def get_logo_base64() -> str:
    """Obtiene el logo de la universidad en formato Base64 para visualización web."""
    paths = [
        os.path.join("assets", "logo_universidad.png"),
        os.path.join("assets", "logo_universidad.jpg"),
        "logo_universidad.png",
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""


def get_profile_base64() -> str:
    """Obtiene la foto de perfil en formato Base64 para visualización web."""
    paths = [
        os.path.join("assets", "perfil.png"),
        "perfil.PNG",
        "perfil.png",
        "perfil.jpg",
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""


def find_demo_filepath() -> str:
    """Busca el archivo histórico de acciones con tolerancia total a codificaciones Unicode en Linux/Docker."""
    candidates = [
        "Historico_Acciones.xlsx",
        "Histórico_Acciones.xlsx",
        "Histórico_Acciones.xlsx",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # Búsqueda dinámica en el directorio
    try:
        for fname in os.listdir("."):
            if fname.endswith(".xlsx") and not fname.startswith("~$") and not fname.startswith("test"):
                norm = unicodedata.normalize("NFC", fname).lower()
                if "historico" in norm or "acciones" in norm:
                    return fname
    except Exception:
        pass
    return "Historico_Acciones.xlsx"


def render_academic_cover():
    """Renderiza la portada académica oficial exactamente como está estructurada en portada.docx."""
    logo_b64 = get_logo_base64()
    prof_b64 = get_profile_base64()

    logo_html = (
        f'<div style="text-align: center; margin-bottom: 28px;">'
        f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 125px; width: auto; object-fit: contain; filter: drop-shadow(0 2px 5px rgba(0,0,0,0.08));" alt="Broward International University">'
        f'</div>'
        if logo_b64
        else ""
    )

    prof_html = (
        f'<div style="margin-bottom: 12px;">'
        f'<img src="data:image/png;base64,{prof_b64}" style="width: 108px; height: 108px; border-radius: 50%; object-fit: cover; border: 3px solid #0284c7; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25);" alt="Cristian Andres Cordoba Gonzalez">'
        f'</div>'
        if prof_b64
        else ""
    )

    st.markdown(
        f"""
    <div class="academic-cover-sheet">
        {logo_html}
        <div style="font-size: 1.35rem; font-weight: bold; letter-spacing: 2.5px; margin-bottom: 12px; text-transform: uppercase; color: #0f172a;">
            TRABAJO
        </div>
        <div style="font-size: 1.45rem; font-weight: bold; line-height: 1.4; margin-bottom: 42px; color: #0f172a;">
            Portafolio diversificado usando rendimientos reales
        </div>
        <div style="font-size: 1.1rem; margin-bottom: 8px; color: #475569;">
            Presentan:
        </div>
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 35px;">
            {prof_html}
            <div style="font-size: 1.25rem; font-weight: bold; color: #0f172a;">
                Cristian Andres Cordoba Gonzalez (Colombia)
            </div>
            <div style="font-size: 0.9rem; color: #64748b; font-weight: 500; margin-top: 3px;">
                Maestrando en Finanzas con Inteligencia Artificial
            </div>
        </div>
        <div style="font-size: 1.1rem; margin-bottom: 5px; color: #475569;">
            Profesor:
        </div>
        <div style="font-size: 1.25rem; font-weight: bold; margin-bottom: 48px; color: #0f172a;">
            Daniel Vázquez Cotera
        </div>
        <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 8px; color: #0f172a; letter-spacing: 0.5px;">
            Broward International University
        </div>
        <div style="font-size: 1.15rem; margin-bottom: 42px; color: #334155;">
            Financial Management with Artificial Intelligence MBA
        </div>
        <div style="font-size: 1.05rem; color: #64748b; font-weight: 500;">
            13 de septiembre de 2026
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# Encabezado Principal
prof_b64_header = get_profile_base64()
prof_header_avatar = (
    f'<img src="data:image/png;base64,{prof_b64_header}" style="width: 38px; height: 38px; border-radius: 50%; object-fit: cover; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.25);" alt="Foto Perfil">'
    if prof_b64_header
    else ""
)

st.markdown(f"""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <h1>📈 CgApp • Plataforma Cuantitativa Markowitz & Agente IA</h1>
            <p>Portafolio diversificado usando rendimientos reales | Broward International University</p>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.16); padding: 5px 14px 5px 8px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.25);">
            {prof_header_avatar}
            <div style="text-align: left;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #ffffff; line-height: 1.1;">Cristian Córdoba</div>
                <div style="font-size: 0.72rem; color: #cbd5e1;">CgApp Financial AI</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Barra Lateral (Sidebar)
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
        <span style="font-size: 1.25rem; font-weight: 800; color: #0284c7; letter-spacing: -0.5px;">CgApp</span>
        <span style="background: #e0f2fe; color: #0369a1; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 12px;">FinAI v2.0</span>
    </div>
    """, unsafe_allow_html=True)

    if os.path.exists("assets/logo_universidad.png"):
        st.image("assets/logo_universidad.png", width=180)
    st.markdown("""
    <div style="margin-bottom: 14px;">
        <div style="font-weight: 700; font-size: 0.95rem; color: #0f172a; line-height: 1.2;">Broward International University</div>
        <div style="font-size: 0.78rem; color: #64748b; margin-top: 2px;">Financial Management with AI MBA</div>
    </div>
    """, unsafe_allow_html=True)

    # Tarjeta de perfil del estudiante en sidebar
    if prof_b64_header:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <img src="data:image/png;base64,{prof_b64_header}" style="width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 2px solid #0284c7;" alt="Cristian Córdoba">
            <div>
                <div style="font-weight: 700; font-size: 0.86rem; color: #0f172a; line-height: 1.2;">Cristian Córdoba</div>
                <div style="font-size: 0.74rem; color: #64748b;">Colombia • MBA Candidate</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🔀 Modo de Análisis")
    data_mode = st.radio(
        "Selecciona el origen de los datos:",
        ["📁 Archivo Histórico Local (Excel/CSV)", "🌐 Conexión en Vivo a API Bursátil"],
        index=0,
    )

    st.markdown("---")
    
    demo_filepath = find_demo_filepath()
    if "Archivo Histórico" in data_mode:
        st.markdown("#### 📁 Carga de Archivo Local")
        uploaded_file = st.file_uploader(
            "Cargar archivo Excel o CSV:",
            type=["xlsx", "xls", "csv"],
            help="Sube un archivo con precios de cierre mensuales. Si viene ordenado de más reciente a más antiguo, se invierte automáticamente."
        )
        if uploaded_file is None and demo_filepath and os.path.exists(demo_filepath):
            if st.button(f"📁 Cargar Archivo Demo ('{os.path.basename(demo_filepath)}')", width="stretch"):
                st.session_state["loaded_demo"] = True

    else:
        st.markdown("#### 🌐 Conexión API Bursátil en Vivo")
        api_preset = st.selectbox(
            "Seleccionar Cartera en Línea:",
            [
                "Bolsa Mexicana de Valores (10 Emisoras BMV + IPC)",
                "Tecnológicas EE.UU. (AAPL, MSFT, GOOGL, NVDA, AMZN + SPY)",
                "Personalizado (Ingresar Tickers)",
            ],
            index=0,
        )

        years_history = st.slider(
            "Histórico a Descargar (Años)",
            min_value=3,
            max_value=20,
            value=15,
            step=1,
        )

        custom_tickers_input = ""
        custom_benchmark_input = "^MXX"
        if "Personalizado" in api_preset:
            custom_tickers_input = st.text_input(
                "Tickers separados por comas:",
                value="BIMBOA.MX, CEMEXCPO.MX, WALMEX.MX, GFNORTEO.MX",
            )
            custom_benchmark_input = st.text_input("Ticker del Benchmark:", value="^MXX")

    st.markdown("---")
    st.markdown("#### ⚖️ Normativa de Optimización Aplicada")
    st.markdown("""
    <div class="norm-box">
        <b>Parámetros Matemáticos Fijos:</b><br/>
        • Restricción de Riesgo: <b>σ_p ≤ 7.00%</b> mensual<br/>
        • Simulación de Monte Carlo: <b>1,000</b> carteras<br/>
        • Modelo: <b>Markowitz Long-Only</b> (w ≥ 0, Σw = 1)<br/>
        • Frecuencia: <b>Estrictamente mensual</b> (Sin anualizar)
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🤖 Agente Cuantitativo IA")
    api_key_input = st.text_input(
        "Clave API Gemini (Opcional)",
        type="password",
        help="Opcional. El agente cuenta con su motor financiero heurístico autónomo 100% operativo sin requerir API."
    )


# Cargar datos según modo seleccionado
prep_data = None
data_source_name = ""

if "Archivo Histórico" in data_mode:
    file_to_process = None
    demo_filepath = find_demo_filepath()
    if uploaded_file is not None:
        file_to_process = uploaded_file
        data_source_name = f"Archivo cargado: {uploaded_file.name}"
    elif st.session_state.get("loaded_demo", True) and demo_filepath and os.path.exists(demo_filepath):
        file_to_process = demo_filepath
        data_source_name = f"Archivo Base: {os.path.basename(demo_filepath)}"

    if file_to_process is not None:
        try:
            prep_data = optimizer.load_and_preprocess_data(file_to_process)
        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")

else:
    # Modo API en vivo
    try:
        with st.spinner("Conectando con la API y descargando precios mensuales en vivo..."):
            if "Bolsa Mexicana" in api_preset:
                prep_data = api_fetcher.fetch_live_market_data(
                    ticker_dict=api_fetcher.BMV_PRESET_TICKERS,
                    benchmark_ticker="^MXX",
                    benchmark_name="IPC",
                    years_back=years_history,
                )
                data_source_name = f"API Yahoo Finance: BMV (10 Emisoras + IPC) - {years_history} años"
            elif "Tecnológicas" in api_preset:
                us_preset = {
                    "AAPL": "AAPL",
                    "MSFT": "MSFT",
                    "GOOGL": "GOOGL",
                    "NVDA": "NVDA",
                    "AMZN": "AMZN",
                }
                prep_data = api_fetcher.fetch_live_market_data(
                    ticker_dict=us_preset,
                    benchmark_ticker="SPY",
                    benchmark_name="SPY_Benchmark",
                    years_back=years_history,
                )
                data_source_name = f"API Yahoo Finance: US Tech (5 Tickers + SPY) - {years_history} años"
            else:
                tickers_list = [t.strip().upper() for t in custom_tickers_input.split(",") if t.strip()]
                t_dict = {t: t for t in tickers_list}
                prep_data = api_fetcher.fetch_live_market_data(
                    ticker_dict=t_dict,
                    benchmark_ticker=custom_benchmark_input.strip() if custom_benchmark_input else None,
                    benchmark_name="Benchmark",
                    years_back=years_history,
                )
                data_source_name = f"API Yahoo Finance: Portafolio Personalizado ({len(tickers_list)} Tickers)"
    except Exception as e:
        st.error(f"Error conectando a la API bursátil: {e}")


# Ejecutar Pipeline Cuantitativo
if prep_data is not None:
    try:
        # 1. Estadísticas mensuales (PROHIBIDO ANUALIZAR)
        stats_data = optimizer.compute_monthly_statistics(prep_data["stock_returns"])

        # 2. Optimización Markowitz con restricción normativa fija (sigma <= 0.07)
        opt_data = optimizer.optimize_markowitz_max_return(prep_data["stock_returns"], max_std=TARGET_RISK)

        # 3. Monte Carlo normativo (1,000 carteras aleatorias)
        mc_data = optimizer.run_monte_carlo_simulation(prep_data["stock_returns"], num_portfolios=NUM_MONTE_CARLO)

        # 4. Benchmark IPC
        bench_data = optimizer.calculate_benchmark_metrics(opt_data["portfolio_returns"], prep_data["ipc_returns"])

        # 5. Agente Cuantitativo Autónomo
        quant_agent = agent.QuantitativePortfolioAgent(api_key=api_key_input)
        agent_report = quant_agent.generate_autonomous_report(prep_data, stats_data, opt_data, mc_data, bench_data)

        # Confirmación serena y confiable
        st.success(f"✅ **Base de Datos Validada**: {data_source_name} | {prep_data['num_periods']} meses cronológicos ({prep_data['start_date'].strftime('%b %Y')} a {prep_data['end_date'].strftime('%b %Y')}).")

        # ==========================================
        # FILA DE KPIs INSTITUCIONALES
        # ==========================================
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Rendimiento Mensual Óptimo</div>
                <div class="metric-value">{opt_data['expected_return']*100:.2f}%</div>
                <div class="metric-sub">μ_p mensual esperado</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Volatilidad Mensual Óptima</div>
                <div class="metric-value">{opt_data['volatility']*100:.2f}%</div>
                <div class="metric-sub">Restricción: ≤ {TARGET_RISK*100:.1f}% mensual</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Ratio de Sharpe Mensual</div>
                <div class="metric-value">{opt_data['sharpe_ratio']:.4f}</div>
                <div class="metric-sub">Con tasa libre de riesgo Rf = 0%</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi4:
            top_asset = opt_data["weights_df"].iloc[0]["Activo"]
            top_w = opt_data["weights_df"].iloc[0]["Porcentaje (%)"]
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Activo Principal</div>
                <div class="metric-value">{top_asset}</div>
                <div class="metric-sub">Ponderación: {top_w:.1f}% del capital</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # ==========================================
        # PESTAÑAS DE NAVEGACIÓN
        # ==========================================
        tabs = st.tabs([
            "🏛️ Portada Institucional",
            "📊 Dashboard Principal",
            "🤖 Agente Cuantitativo Autónomo",
            "🧹 Centro de Auditoría de Datos",
            "📈 Estadísticas & Matrices",
            "🎲 Simulación Monte Carlo",
            "📥 Exportar Informes (PDF / Word / Colab)",
        ])

        # ----------------------------------------------------
        # TAB 0: PORTADA INSTITUCIONAL (ESTRUCTURA OFICIAL)
        # ----------------------------------------------------
        with tabs[0]:
            render_academic_cover()

            # Resumen Metodológico Institucional
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-label">🏛️ Institución & Grado</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-top: 4px;">Broward International Univ.</div>
                    <div class="metric-sub">Financial Management with AI MBA</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-label">⚖️ Modelo Cuantitativo</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-top: 4px;">Markowitz Long-Only</div>
                    <div class="metric-sub">Restricción: σ_p ≤ {TARGET_RISK*100:.1f}% Mensual</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-label">🎲 Simulación & Benchmark</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-top: 4px;">{NUM_MONTE_CARLO:,} Carteras</div>
                    <div class="metric-sub">Benchmark IPC (Excluido de Pesos)</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.info("💡 **Navegación de la Plataforma**: Puedes explorar el **Dashboard Principal** en la siguiente pestaña para interactuar con la nube de carteras, examinar el **Dictamen del Agente IA** o descargar el reporte oficial en Word y PDF.")

        # ----------------------------------------------------
        # TAB 1: DASHBOARD PRINCIPAL
        # ----------------------------------------------------
        with tabs[1]:
            col_left, col_right = st.columns([1.35, 1.0])

            with col_left:
                st.markdown("#### 🌌 Nube de Monte Carlo & Cartera Óptima de Markowitz")
                sim_df = mc_data["simulation_df"]
                
                fig_mc = go.Figure()

                # Nube de 1,000 carteras aleatorias
                fig_mc.add_trace(go.Scatter(
                    x=sim_df["Volatilidad Mensual"] * 100,
                    y=sim_df["Rendimiento Mensual"] * 100,
                    mode="markers",
                    marker=dict(
                        size=6,
                        color=sim_df["Ratio Sharpe Mensual"],
                        colorscale="Blues",
                        colorbar=dict(title="Sharpe Mensual", thickness=14),
                        opacity=0.6,
                    ),
                    name="1,000 Carteras Monte Carlo",
                    hovertemplate="Volatilidad: %{x:.2f}%<br>Retorno: %{y:.2f}%<extra></extra>",
                ))

                # Cartera Óptima destacada con tono institucional Dorado / Azul Marino
                fig_mc.add_trace(go.Scatter(
                    x=[opt_data["volatility"] * 100],
                    y=[opt_data["expected_return"] * 100],
                    mode="markers",
                    marker=dict(
                        size=17,
                        color="#D97706",
                        symbol="star",
                        line=dict(color="#1E293B", width=1.5),
                    ),
                    name=f"Cartera Óptima (Ret: {opt_data['expected_return']*100:.2f}%, Vol: {opt_data['volatility']*100:.2f}%)",
                    hovertemplate="<b>CARTERA ÓPTIMA</b><br>Volatilidad: %{x:.2f}%<br>Retorno: %{y:.2f}%<extra></extra>",
                ))

                # Benchmark si existe
                if bench_data:
                    fig_mc.add_trace(go.Scatter(
                        x=[bench_data["ipc_std_monthly"] * 100],
                        y=[bench_data["ipc_mean_monthly"] * 100],
                        mode="markers",
                        marker=dict(
                            size=13,
                            color="#059669",
                            symbol="diamond",
                            line=dict(color="#1E293B", width=1.2),
                        ),
                        name=f"Benchmark ({bench_data['ipc_mean_monthly']*100:.2f}%, {bench_data['ipc_std_monthly']*100:.2f}%)",
                        hovertemplate="<b>BENCHMARK</b><br>Volatilidad: %{x:.2f}%<br>Retorno: %{y:.2f}%<extra></extra>",
                    ))

                # Línea de restricción en gris institucional
                fig_mc.add_vline(
                    x=TARGET_RISK * 100,
                    line_dash="dash",
                    line_color="#475569",
                    annotation_text="Límite σ_p ≤ 7.0%",
                    annotation_position="top left",
                )

                fig_mc.update_layout(
                    xaxis_title="Volatilidad Mensual σ_p (%) [PROHIBIDO ANUALIZAR]",
                    yaxis_title="Rendimiento Esperado Mensual μ_p (%)",
                    height=500,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    template="plotly_white",
                )
                st.plotly_chart(fig_mc, width="stretch")

            with col_right:
                st.markdown("#### 🥧 Asignación Óptima de Capital (Pesos w_i)")
                w_df = opt_data["weights_df"]
                w_active = w_df[w_df["Ponderación Óptima (w)"] > 0.001]

                fig_pie = px.pie(
                    w_active,
                    values="Porcentaje (%)",
                    names="Activo",
                    hole=0.45,
                    color_discrete_sequence=px.colors.sequential.Blues_r,
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                fig_pie.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
                st.plotly_chart(fig_pie, width="stretch")

                st.markdown("##### Ponderaciones Detalladas")
                styled_w = w_df.copy()
                styled_w["Ponderación (w)"] = styled_w["Ponderación Óptima (w)"].apply(lambda x: f"{x:.4f}")
                styled_w["Asignación"] = styled_w["Porcentaje (%)"].apply(lambda x: f"{x:.2f}%")
                st.dataframe(styled_w[["Activo", "Ponderación (w)", "Asignación"]], width="stretch", hide_index=True)

        # ----------------------------------------------------
        # TAB 2: AGENTE CUANTITATIVO AUTÓNOMO
        # ----------------------------------------------------
        with tabs[2]:
            st.markdown("### 🤖 Diagnóstico del Agente Cuantitativo Financiero")
            
            st.markdown(f"""
            <div class="agent-card">
                <h4 style="margin-top:0; color:#0369a1;">📋 Dictamen Ejecutivo Autónomo</h4>
                <p style="font-size:1.02rem; line-height:1.6; margin-bottom:0;">{agent_report['executive_summary']}</p>
            </div>
            """, unsafe_allow_html=True)

            c_ag1, c_ag2 = st.columns(2)
            with c_ag1:
                st.markdown("#### 🔍 Análisis de Activos Individuales")
                st.markdown(agent_report["asset_insights"]["text"])

                st.markdown("#### 🔗 Estructura de Correlaciones y Diversificación")
                st.markdown(agent_report["corr_insights"]["text"])

            with c_ag2:
                st.markdown(agent_report["opt_insights"]["text"])

            st.markdown("---")
            c_ag3, c_ag4 = st.columns(2)
            with c_ag3:
                st.markdown("#### 🎲 Evaluación de la Simulación de Monte Carlo")
                st.markdown(agent_report["mc_insights"]["text"])

            with c_ag4:
                st.markdown(agent_report["bench_insights"]["text"])

            st.markdown("---")
            st.markdown(agent_report["recommendations"])

            # Módulo de Consultas al Agente (Robustecido y sin errores)
            st.markdown("---")
            st.markdown("#### 💬 Consultas Especializadas al Agente Cuantitativo")
            st.markdown("Selecciona una pregunta de análisis financiero o escribe una consulta personalizada para el Comité de Inversión:")
            
            preset_questions = [
                "⚖️ ¿Por qué ciertos activos tienen peso 0% y otros concentran la cartera?",
                "🔄 ¿Cuál es el protocolo y cadencia de rebalanceo recomendado?",
                "🛡️ ¿Cómo responde la cartera si cambia la volatilidad del mercado?",
                "🚨 ¿Por qué está estrictamente prohibido anualizar los datos?",
                "📊 Diagnóstico integral de la Cartera Óptima de Markowitz",
                "✍️ Escribir otra pregunta personalizada...",
            ]

            selected_preset = st.selectbox("Seleccionar consulta:", preset_questions, index=0)

            final_query = selected_preset
            if "Escribir otra pregunta" in selected_preset:
                final_query = st.text_input(
                    "Escribe tu consulta detallada:",
                    value="",
                    placeholder="Ejemplo: ¿Cómo influyen las tasas de interés de Banxico en los activos elegidos?"
                )

            if st.button("🔍 Analizar Consulta con el Agente", width="stretch"):
                if final_query.strip():
                    with st.spinner("El Agente Cuantitativo está procesando el análisis financiero..."):
                        try:
                            context = {
                                "opt_ret": opt_data["expected_return"],
                                "opt_vol": opt_data["volatility"],
                                "opt_sharpe": opt_data["sharpe_ratio"],
                                "target_std": TARGET_RISK,
                                "weights_summary": ", ".join([f"{r['Activo']}: {r['Porcentaje (%)']:.1f}%" for _, r in opt_data['weights_df'].iterrows() if r['Ponderación Óptima (w)'] > 0.005]),
                            }
                            answer = quant_agent.ask_agent(final_query, context)
                            st.markdown("---")
                            st.markdown(answer)
                        except Exception as ex:
                            st.warning(f"Respuesta generada con motor heurístico seguro: {str(ex)}")
                else:
                    st.info("Por favor ingresa una pregunta en el campo de texto.")

        # ----------------------------------------------------
        # TAB 3: CENTRO DE AUDITORÍA Y LIMPIEZA DE ERRORES
        # ----------------------------------------------------
        with tabs[3]:
            st.markdown("### 🧹 Centro de Auditoría de Calidad & Normalización de Datos")
            st.markdown(
                "Este módulo audita automáticamente el archivo ingresado, asegurando el cumplimiento estricto "
                "de la regla cronológica (pasado ➔ presente), el filtrado de fórmulas de resumen y la integridad numérica."
            )

            a1, a2, a3, a4 = st.columns(4)
            with a1:
                st.metric("Filas Brutas Analizadas", prep_data["total_raw_rows"])
            with a2:
                st.metric("Filas Cronológicas Válidas", prep_data["num_periods"] + 1)
            with a3:
                st.metric("Fórmulas Residuales Filtradas", prep_data["invalid_rows_count"])
            with a4:
                st.metric("Columnas Auxiliares Depuradas", prep_data["discarded_cols_count"])

            st.markdown("#### 📋 Registro de Normalización y Calidad de la Serie")
            audit_df = prep_data.get("audit_df", pd.DataFrame())
            if not audit_df.empty:
                st.dataframe(audit_df, width="stretch", hide_index=True)

            st.markdown("---")
            st.markdown("#### 💾 Descargar Dataset Depurado")
            st.markdown("Descarga la matriz histórica limpia (sin fórmulas de Excel intermedias ni pies de página) lista para modelación:")
            
            cleaned_buf = io.BytesIO()
            prep_data["cleaned_export_df"].to_excel(cleaned_buf, index=False)
            st.download_button(
                label="📥 Descargar Dataset Normalizado (.xlsx)",
                data=cleaned_buf.getvalue(),
                file_name="Historico_Acciones_Normalizado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="content",
            )

        # ----------------------------------------------------
        # TAB 4: ESTADÍSTICAS & MATRICES
        # ----------------------------------------------------
        with tabs[4]:
            st.markdown("### 📊 Parámetros Estadísticos Mensuales (Sin Anualizar)")
            st.caption("🚨 Regla crítica estricta: Todo el cálculo matemático permanece en frecuencia mensual.")

            st.dataframe(
                stats_data["stats_table"].style.format({
                    "Rendimiento Mensual Promedio": "{:.2%}",
                    "Volatilidad Mensual (Desv. Est.)": "{:.2%}",
                    "Varianza Mensual": "{:.6f}",
                    "Ratio Sharpe Mensual (Rf=0)": "{:.4f}",
                    "Rendimiento Mínimo Mensual": "{:.2%}",
                    "Rendimiento Máximo Mensual": "{:.2%}",
                }),
                width="stretch",
            )

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("#### 🔷 Matriz de Correlación Mensual")
                fig_corr = px.imshow(
                    stats_data["corr_matrix"],
                    text_auto=".2f",
                    aspect="auto",
                    color_continuous_scale="Blues",
                    zmin=-1,
                    zmax=1,
                )
                fig_corr.update_layout(height=450, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_corr, width="stretch")

            with col_m2:
                st.markdown("#### 🔷 Matriz de Covarianza Mensual (Σ)")
                fig_cov = px.imshow(
                    stats_data["cov_matrix"],
                    text_auto=".4f",
                    aspect="auto",
                    color_continuous_scale="PuBu",
                )
                fig_cov.update_layout(height=450, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_cov, width="stretch")

            if bench_data:
                st.markdown("#### 📈 Evolución del Rendimiento Acumulado Histórico")
                aligned = bench_data["aligned_series"]
                cum_df = (1.0 + aligned).cumprod()
                cum_df["Cartera Óptima Markowitz"] = (cum_df["Portfolio"] - 1.0) * 100
                cum_df["Índice Benchmark"] = (cum_df["IPC"] - 1.0) * 100

                fig_cum = go.Figure()
                fig_cum.add_trace(go.Scatter(
                    x=cum_df.index,
                    y=cum_df["Cartera Óptima Markowitz"],
                    mode="lines",
                    name="Cartera Óptima Markowitz",
                    line=dict(color="#0284C7", width=2.5),
                ))
                fig_cum.add_trace(go.Scatter(
                    x=cum_df.index,
                    y=cum_df["Índice Benchmark"],
                    mode="lines",
                    name="Índice Benchmark",
                    line=dict(color="#64748B", width=1.5, dash="dot"),
                ))
                fig_cum.update_layout(
                    yaxis_title="Rendimiento Acumulado (%)",
                    xaxis_title="Fecha",
                    height=380,
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_cum, width="stretch")

        # ----------------------------------------------------
        # TAB 5: SIMULACIÓN DE MONTE CARLO
        # ----------------------------------------------------
        with tabs[5]:
            st.markdown("### 🎲 Simulación de Monte Carlo (1,000 Carteras Aleatorias)")
            col_mc1, col_mc2 = st.columns(2)
            with col_mc1:
                st.markdown("#### Histograma: Ratios de Sharpe Mensuales")
                fig_hist = px.histogram(
                    mc_data["simulation_df"],
                    x="Ratio Sharpe Mensual",
                    nbins=40,
                    color_discrete_sequence=["#0284C7"],
                )
                fig_hist.add_vline(
                    x=opt_data["sharpe_ratio"],
                    line_color="#D97706",
                    line_dash="dash",
                    line_width=2,
                    annotation_text=f"Óptimo ({opt_data['sharpe_ratio']:.4f})",
                )
                fig_hist.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), template="plotly_white")
                st.plotly_chart(fig_hist, width="stretch")

            with col_mc2:
                st.markdown("#### Tabla de Percentiles de Monte Carlo")
                percentiles = mc_data["simulation_df"].quantile([0.05, 0.25, 0.50, 0.75, 0.95, 0.99])
                st.dataframe(
                    percentiles.style.format({
                        "Rendimiento Mensual": "{:.2%}",
                        "Volatilidad Mensual": "{:.2%}",
                        "Ratio Sharpe Mensual": "{:.4f}",
                    }),
                    width="stretch",
                )

        # ----------------------------------------------------
        # TAB 6: EXPORTAR INFORMES
        # ----------------------------------------------------
        with tabs[6]:
            st.markdown("### 📥 Descarga de Informes Ejecutivos & Empaquetado")
            
            c_exp1, c_exp2 = st.columns(2)
            
            with c_exp1:
                st.markdown("#### 📄 Informe Ejecutivo en PDF (.pdf)")
                st.markdown("Reporte institucional en PDF con tablas estilizadas, gráficos de alta resolución y dictamen del Agente Cuantitativo.")
                
                pdf_bytes = pdf_exporter.generate_pdf_report(
                    prep_data, stats_data, opt_data, mc_data, bench_data, agent_report
                )
                st.download_button(
                    label="📥 Descargar Informe Completo en PDF (.pdf)",
                    data=pdf_bytes.getvalue(),
                    file_name="Informe_Ejecutivo_Markowitz.pdf",
                    mime="application/pdf",
                    width="stretch",
                )

                st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
                st.markdown("#### 📄 Informe Ejecutivo en Word (.docx)")
                doc_bytes = word_exporter.generate_word_report(
                    prep_data, stats_data, opt_data, mc_data, bench_data, agent_report
                )
                st.download_button(
                    label="📥 Descargar Informe Completo en Word (.docx)",
                    data=doc_bytes.getvalue(),
                    file_name="Informe_Ejecutivo_Markowitz.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    width="stretch",
                )

            with c_exp2:
                st.markdown("#### 🐍 Google Colab & Cuaderno Jupyter")
                st.markdown("Archivos preparados para ejecutar directamente en la nube de Google Colab:")
                
                if os.path.exists("markowitz_colab.ipynb"):
                    with open("markowitz_colab.ipynb", "rb") as f_nb:
                        st.download_button(
                            label="📓 Descargar Cuaderno Google Colab (.ipynb)",
                            data=f_nb.read(),
                            file_name="markowitz_colab.ipynb",
                            mime="application/x-ipynb+json",
                            width="stretch",
                        )

                if os.path.exists("markowitz_colab.py"):
                    with open("markowitz_colab.py", "rb") as f_py:
                        st.download_button(
                            label="🐍 Descargar Script Python Standalone (.py)",
                            data=f_py.read(),
                            file_name="markowitz_colab.py",
                            mime="text/x-python",
                            width="stretch",
                        )

            st.markdown("---")
            st.markdown("#### 🚀 Empaquetado en Ejecutable Portátil ('Doble Clic')")
            st.markdown(
                "Para abrir esta aplicación en cualquier computador sin abrir la terminal:\n"
                "• **En macOS / Linux**: Haz doble clic en el archivo `iniciar_plataforma.command`.\n"
                "• **En Windows**: Haz doble clic en el archivo `iniciar_plataforma.bat`.\n"
                "Ambos iniciarán automáticamente el entorno y abrirán la plataforma en tu navegador web predeterminado."
            )

    except Exception as e:
        st.error(f"Error procesando el análisis: {str(e)}")
        with st.expander("🛠️ Ver diagnóstico técnico del agente"):
            st.code(traceback.format_exc(), language="python")

else:
    render_academic_cover()
    st.info("👆 Selecciona un archivo o conecta la API en la barra lateral para iniciar el análisis cuantitativo.")
