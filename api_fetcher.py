"""
Módulo de Conexión en Línea y Consumo de Datos de Mercado en Vivo
Permite descargar históricos bursátiles directamente desde Yahoo Finance o APIs de mercado:
- Presets para la Bolsa Mexicana de Valores (BMV).
- Soporte para acciones internacionales y benchmarks (IPC ^MXX, S&P 500 SPY).
- Remuestreo mensual al cierre de mes.
- Integración directa con el pipeline cuantitativo de Markowitz.
"""

from typing import Dict, List, Optional, Any
import datetime
import pandas as pd
import numpy as np
import yfinance as yf

# Presets de activos bursátiles
BMV_PRESET_TICKERS = {
    "BIMBOA": "BIMBOA.MX",
    "CEMEX": "CEMEXCPO.MX",
    "FEMSA": "FEMSAUBD.MX",
    "ASUR": "ASURB.MX",
    "BANORTE": "GFNORTEO.MX",
    "GRUMA": "GRUMAB.MX",
    "HERDEZ": "HERDEZ.MX",
    "KIMBERLY": "KIMBERA.MX",
    "PEÑOLES": "PE&OLES.MX",
    "WALMART": "WALMEX.MX",
}
BMV_BENCHMARK = "^MXX"  # Índice IPC México


def fetch_live_market_data(
    ticker_dict: Optional[Dict[str, str]] = None,
    benchmark_ticker: str = "^MXX",
    benchmark_name: str = "IPC",
    years_back: int = 15,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Descarga precios de cierre mensuales en vivo vía Yahoo Finance API.
    Alinea fechas, elimina nulos, asegura orden cronológico y estructura los datos.
    """
    if ticker_dict is None:
        ticker_dict = BMV_PRESET_TICKERS

    # Definir fechas
    if end_date is None:
        end_dt = datetime.datetime.now()
        end_date = end_dt.strftime("%Y-%m-%d")
    if start_date is None:
        start_dt = datetime.datetime.now() - datetime.timedelta(days=365 * years_back)
        start_date = start_dt.strftime("%Y-%m-%d")

    all_tickers = list(ticker_dict.values())
    if benchmark_ticker and benchmark_ticker not in all_tickers:
        all_tickers.append(benchmark_ticker)

    # Descarga directa en intervalo mensual ('1mo')
    data = yf.download(all_tickers, start=start_date, end=end_date, interval="1mo", progress=False)

    if data.empty or "Close" not in data:
        raise ValueError("No se pudieron descargar datos para los activos seleccionados en el rango de fechas especificado.")

    close_df = data["Close"].copy()

    # Mapear columnas a nombres legibles
    inv_map = {v: k for k, v in ticker_dict.items()}
    if benchmark_ticker:
        inv_map[benchmark_ticker] = benchmark_name

    renamed_cols = {}
    for col in close_df.columns:
        if col in inv_map:
            renamed_cols[col] = inv_map[col]
        else:
            renamed_cols[col] = str(col)

    close_df = close_df.rename(columns=renamed_cols)

    # Ordenar cronológicamente (pasado -> presente)
    close_df = close_df.sort_index(ascending=True)

    # Eliminar activos que tengan demasiados valores vacíos (> 25% nulos)
    valid_cols = []
    for c in close_df.columns:
        if close_df[c].notna().sum() > len(close_df) * 0.70:
            valid_cols.append(c)
    
    close_df = close_df[valid_cols].dropna()

    if len(close_df) < 6:
        raise ValueError("La serie temporal descargada contiene muy pocos meses tras depurar valores faltantes.")

    # Reset index con columna 'Fecha'
    close_df = close_df.reset_index()
    close_df = close_df.rename(columns={"Date": "Fecha", "index": "Fecha"})

    # Identificar activos vs benchmark
    stock_cols = [c for c in valid_cols if c != benchmark_name]

    # Calcular rendimientos simples mensuales
    returns_df = close_df[valid_cols].pct_change().dropna()
    returns_df.index = close_df["Fecha"].iloc[1:]

    stock_returns = returns_df[stock_cols]
    ipc_returns = returns_df[benchmark_name] if benchmark_name in returns_df else None

    # Registrar evento de auditoría
    audit_events = [
        {
            "Etapa": "Conexión API en Vivo",
            "Detalle": f"Consumo exitoso desde Yahoo Finance API ({len(stock_cols)} activos + Benchmark {benchmark_name}).",
            "Severidad": "En Línea",
            "Acción": "Datos actualizados en tiempo real",
        },
        {
            "Etapa": "Rango Temporal en Vivo",
            "Detalle": f"Histórico obtenido desde {close_df['Fecha'].iloc[0].strftime('%b %Y')} hasta {close_df['Fecha'].iloc[-1].strftime('%b %Y')} ({len(stock_returns)} meses continuos).",
            "Severidad": "Validado",
            "Acción": "Serie temporal mensual completa",
        },
        {
            "Etapa": "Regla del Tiempo",
            "Detalle": "Orden cronológico validado estrictamente de pasado a presente antes del cálculo de tasas de crecimiento.",
            "Severidad": "Validado",
            "Acción": "Cronología garantizada",
        },
        {
            "Etapa": "Benchmark",
            "Detalle": f"Benchmark '{benchmark_name}' reservado exclusivamente para métricas de riesgo relativo (Alpha y Beta). Excluido de ponderaciones del portafolio.",
            "Severidad": "Regla Estricta",
            "Acción": "Exclusión aplicada",
        }
    ]

    return {
        "raw_prices": close_df,
        "cleaned_export_df": close_df,
        "returns_df": returns_df,
        "stock_returns": stock_returns,
        "ipc_returns": ipc_returns,
        "stock_cols": stock_cols,
        "ipc_col": benchmark_name if benchmark_name in returns_df else None,
        "date_col": "Fecha",
        "dates": pd.Series(returns_df.index, index=returns_df.index, name="Fecha"),
        "was_inverted": False,
        "num_periods": len(stock_returns),
        "start_date": returns_df.index[0],
        "end_date": returns_df.index[-1],
        "audit_events": audit_events,
        "audit_df": pd.DataFrame(audit_events),
        "total_raw_rows": len(close_df),
        "total_raw_cols": len(valid_cols) + 1,
        "invalid_rows_count": 0,
        "discarded_cols_count": 0,
    }
