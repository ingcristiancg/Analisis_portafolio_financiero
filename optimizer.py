"""
Módulo de Optimización Cuantitativa y Teoría de Carteras de Markowitz
Reglas Estrictas:
1. Orden cronológico obligatorio (pasado -> presente) antes de calcular rendimientos.
2. Rendimientos simples mensuales: R_t = (P_t - P_{t-1}) / P_{t-1}.
3. Exclusión estricta del IPC en la optimización.
4. Parámetros estadísticos estrictamente mensuales (PROHIBIDO ANUALIZAR).
5. Función objetivo: Maximizar rendimiento mensual sujeto a desviación mensual <= 0.07, sum(w)=1, w>=0.
6. Simulación de Monte Carlo: 1,000 carteras aleatorias.
7. Centro de Auditoría de Calidad y Normalización de Datos.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy.optimize import minimize


def load_and_preprocess_data(
    file_or_path: Any,
    sheet_name: Optional[Any] = None,
    date_col_name: Optional[str] = None,
    ipc_col_name: str = "IPC",
) -> Dict[str, Any]:
    """
    Carga y preprocesa el archivo Excel/CSV aplicando estrictamente:
    - Registro de auditoría y normalización de calidad de datos.
    - Detección de columnas de precios y fechas.
    - REGLA DEL TIEMPO CRÍTICA: Asegura orden cronológico (pasado -> presente).
      Si viene ordenado con la fecha más reciente arriba, lo invierte.
    - Cálculo de rendimientos simples mensuales.
    - Exclusión del IPC para la optimización de activos.
    - Eliminación de NaNs y normalización de series temporales.
    """
    audit_events = []
    
    # 1. Lectura del archivo
    if isinstance(file_or_path, str) and file_or_path.endswith((".csv", ".txt")):
        raw_df = pd.read_csv(file_or_path)
        sheet_used = "CSV"
    else:
        xl = pd.ExcelFile(file_or_path)
        if sheet_name is None:
            target_sheet = xl.sheet_names[0]
            for s in ["report", "Precios", "Prices", "Crecimiento"]:
                if s in xl.sheet_names:
                    target_sheet = s
                    break
            sheet_name = target_sheet
        sheet_used = sheet_name
        raw_df = pd.read_excel(file_or_path, sheet_name=sheet_name)

    total_raw_rows = len(raw_df)
    total_raw_cols = len(raw_df.columns)

    audit_events.append({
        "Fase del Proceso": "Ingestión de Datos",
        "Descripción Cuantitativa": f"Lectura de archivo completada. Hoja: '{sheet_used}'. Filas brutas: {total_raw_rows}, Columnas: {total_raw_cols}.",
        "Estado": "Validado",
        "Tratamiento Aplicado": "Estructura cargada correctamente en memoria"
    })

    # 2. Identificación de la columna de fecha
    if date_col_name is None:
        for c in raw_df.columns:
            c_str = str(c).lower().strip()
            if any(k in c_str for k in ["fecha", "date", "time", "periodo", "mes"]):
                date_col_name = c
                break
        if date_col_name is None:
            date_col_name = raw_df.columns[0]

    audit_events.append({
        "Fase del Proceso": "Estructura Temporal",
        "Descripción Cuantitativa": f"Columna temporal identificada: '{date_col_name}'.",
        "Estado": "Validado",
        "Tratamiento Aplicado": "Configurada como índice cronológico del modelo"
    })

    # 3. Limpieza de filas no numéricas o pies de página
    df_clean = raw_df.copy()
    df_clean["__parsed_date__"] = pd.to_datetime(df_clean[date_col_name], errors="coerce")
    
    invalid_date_mask = df_clean["__parsed_date__"].isna()
    invalid_rows_count = invalid_date_mask.sum()
    
    if invalid_rows_count > 0:
        dropped_samples = df_clean.loc[invalid_date_mask, date_col_name].dropna().unique().tolist()[:5]
        audit_events.append({
            "Fase del Proceso": "Filtrado de Resúmenes Residuales",
            "Descripción Cuantitativa": f"Se depuraron {invalid_rows_count} filas con fórmulas de resumen o textos de pie de página: {dropped_samples}.",
            "Estado": "Normalizado",
            "Tratamiento Aplicado": "Excluidas para garantizar una serie temporal estrictamente mensual"
        })
        df_clean = df_clean[~invalid_date_mask].copy()

    if len(df_clean) < 2:
        raise ValueError("El archivo no contiene suficientes observaciones temporales válidas para calcular rendimientos mensuales.")

    # 4. REGLA DEL TIEMPO CRÍTICA:
    first_date = df_clean["__parsed_date__"].iloc[0]
    last_date = df_clean["__parsed_date__"].iloc[-1]
    was_inverted = False

    if first_date > last_date:
        was_inverted = True
        df_clean = df_clean.iloc[::-1].reset_index(drop=True)
        audit_events.append({
            "Fase del Proceso": "Orden Cronológico",
            "Descripción Cuantitativa": f"El archivo presentaba orden descendente ({first_date.strftime('%Y-%m-%d')} a {last_date.strftime('%Y-%m-%d')}).",
            "Estado": "Normalizado",
            "Tratamiento Aplicado": "Reordenado a estricto orden cronológico (pasado en fila 0 -> presente en última fila)"
        })
    else:
        df_clean = df_clean.sort_values(by="__parsed_date__", ascending=True).reset_index(drop=True)
        audit_events.append({
            "Fase del Proceso": "Orden Cronológico",
            "Descripción Cuantitativa": f"Serie temporal validada en orden cronológico ({df_clean['__parsed_date__'].iloc[0].strftime('%Y-%m-%d')} a {df_clean['__parsed_date__'].iloc[-1].strftime('%Y-%m-%d')}).",
            "Estado": "Validado",
            "Tratamiento Aplicado": "Orden cronológico confirmado"
        })

    # 5. Identificación y filtrado de columnas
    all_cols = [c for c in df_clean.columns if c not in [date_col_name, "__parsed_date__"]]
    valid_numeric_cols = []
    discarded_cols = []

    for c in all_cols:
        c_str = str(c).strip()
        if c_str.startswith("Unnamed:") or "proporci" in c_str.lower() or "portafolio" in c_str.lower():
            discarded_cols.append(c)
            continue
        s = pd.to_numeric(df_clean[c], errors="coerce")
        if s.notna().sum() > len(df_clean) * 0.5:
            df_clean[c] = s
            valid_numeric_cols.append(c)
        else:
            discarded_cols.append(c)

    if len(discarded_cols) > 0:
        audit_events.append({
            "Fase del Proceso": "Columnas Auxiliares",
            "Descripción Cuantitativa": f"Se depuraron {len(discarded_cols)} columnas de fórmulas intermedias del archivo original.",
            "Estado": "Normalizado",
            "Tratamiento Aplicado": "Filtradas para conservar únicamente columnas de precios de activos"
        })

    # Separar IPC de las acciones a optimizar
    actual_ipc_col = None
    for c in valid_numeric_cols:
        if ipc_col_name.lower() in str(c).lower().strip():
            actual_ipc_col = c
            break

    if actual_ipc_col:
        audit_events.append({
            "Fase del Proceso": "Benchmark de Mercado (IPC)",
            "Descripción Cuantitativa": f"Columna '{actual_ipc_col}' identificada como índice de mercado.",
            "Estado": "Conforme a Norma",
            "Tratamiento Aplicado": "Excluido 100% de la optimización de activos; reservado para métricas de riesgo relativo"
        })

    stock_cols = [c for c in valid_numeric_cols if c != actual_ipc_col]
    if len(stock_cols) < 2:
        raise ValueError("Se requieren al menos 2 acciones numéricas válidas para optimizar la cartera.")

    audit_events.append({
        "Fase del Proceso": "Universo de Activos",
        "Descripción Cuantitativa": f"{len(stock_cols)} activos validados para el portafolio: {', '.join(stock_cols)}.",
        "Estado": "Validado",
        "Tratamiento Aplicado": "Activos listos para el cálculo de rendimientos y covarianza"
    })

    # 6. Cálculo de rendimientos simples mensuales: R_t = (P_t - P_{t-1}) / P_{t-1}
    prices_df = df_clean[[date_col_name, "__parsed_date__"] + valid_numeric_cols].copy()
    returns_df = df_clean[valid_numeric_cols].pct_change().dropna(how="all")
    returns_df.index = df_clean["__parsed_date__"].iloc[1:]
    
    null_counts = returns_df[stock_cols].isna().sum()
    total_nulls = null_counts.sum()
    if total_nulls > 0:
        audit_events.append({
            "Fase del Proceso": "Consistencia de Datos",
            "Descripción Cuantitativa": f"Se depuraron {total_nulls} celdas no disponibles en la serie.",
            "Estado": "Normalizado",
            "Tratamiento Aplicado": "Alineadas para garantizar matrices de covarianza completas"
        })
    
    returns_df = returns_df.dropna(subset=stock_cols)
    dates_series = pd.Series(returns_df.index, index=returns_df.index, name="Fecha")

    stock_returns = returns_df[stock_cols]
    ipc_returns = returns_df[actual_ipc_col] if actual_ipc_col is not None else None

    audit_df = pd.DataFrame(audit_events)
    cleaned_export_df = df_clean[[date_col_name] + valid_numeric_cols].copy()

    return {
        "raw_prices": prices_df,
        "cleaned_export_df": cleaned_export_df,
        "returns_df": returns_df,
        "stock_returns": stock_returns,
        "ipc_returns": ipc_returns,
        "stock_cols": stock_cols,
        "ipc_col": actual_ipc_col,
        "date_col": date_col_name,
        "dates": dates_series,
        "was_inverted": was_inverted,
        "num_periods": len(stock_returns),
        "start_date": dates_series.iloc[0],
        "end_date": dates_series.iloc[-1],
        "audit_events": audit_events,
        "audit_df": audit_df,
        "total_raw_rows": total_raw_rows,
        "total_raw_cols": total_raw_cols,
        "invalid_rows_count": invalid_rows_count,
        "discarded_cols_count": len(discarded_cols),
    }


def compute_monthly_statistics(stock_returns: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula los parámetros estadísticos mensuales:
    - Media aritmética mensual de rendimientos (mu_i)
    - Desviación estándar mensual (sigma_i)
    - Matriz de covarianza mensual (Sigma)
    - Matriz de correlación mensual
    - Ratios de Sharpe individuales mensuales (Rf = 0)
    🚨 REGLA CRÍTICA: PROHIBIDO ANUALIZAR. Todo es estrictamente mensual.
    """
    mean_monthly = stock_returns.mean()
    std_monthly = stock_returns.std()
    cov_monthly = stock_returns.cov()
    corr_monthly = stock_returns.corr()
    sharpe_monthly = mean_monthly / std_monthly.replace(0, np.nan)

    stats_table = pd.DataFrame({
        "Rendimiento Mensual Promedio": mean_monthly,
        "Volatilidad Mensual (Desv. Est.)": std_monthly,
        "Varianza Mensual": stock_returns.var(),
        "Ratio Sharpe Mensual (Rf=0)": sharpe_monthly,
        "Rendimiento Mínimo Mensual": stock_returns.min(),
        "Rendimiento Máximo Mensual": stock_returns.max(),
    })

    return {
        "mean_returns": mean_monthly,
        "std_devs": std_monthly,
        "cov_matrix": cov_monthly,
        "corr_matrix": corr_monthly,
        "sharpe_ratios": sharpe_monthly,
        "stats_table": stats_table,
    }


def optimize_markowitz_max_return(
    stock_returns: pd.DataFrame,
    max_std: float = 0.07,
) -> Dict[str, Any]:
    """
    Optimización de Markowitz:
    - Función objetivo: Maximizar rendimiento esperado mensual de la cartera (min -w^T * mu).
    - Restricción 1: Desviación estándar mensual de la cartera <= max_std (0.07 mensual).
    - Restricción 2: 100% del capital invertido (sum(w) = 1).
    - Límites: Solo posiciones largas (w_i >= 0, sin ventas en corto).
    """
    mean_returns = stock_returns.mean().values
    cov_matrix = stock_returns.cov().values
    n = len(mean_returns)
    stock_names = stock_returns.columns.tolist()

    def objective_neg_return(w: np.ndarray) -> float:
        return -float(np.dot(w, mean_returns))

    def portfolio_volatility(w: np.ndarray) -> float:
        return float(np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))))

    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {"type": "ineq", "fun": lambda w: max_std - np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))},
    ]

    bounds = tuple((0.0, 1.0) for _ in range(n))
    w0 = np.ones(n) / n

    res = minimize(
        objective_neg_return,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-9},
    )

    if not res.success:
        min_var_res = optimize_minimum_variance(stock_returns)
        min_possible_std = min_var_res["volatility"]
        if max_std < min_possible_std:
            raise ValueError(
                f"La desviación estándar requerida ({max_std:.2%}) es inferior al riesgo mínimo alcanzable "
                f"del mercado para estos activos ({min_possible_std:.2%}). "
                f"Aumenta la restricción a al menos {min_possible_std:.4f}."
            )
        else:
            raise RuntimeError(f"La optimización no convergió: {res.message}")

    optimal_weights = res.x
    optimal_weights = np.where(optimal_weights < 1e-5, 0.0, optimal_weights)
    optimal_weights = optimal_weights / np.sum(optimal_weights)

    opt_return = float(np.dot(optimal_weights, mean_returns))
    opt_vol = portfolio_volatility(optimal_weights)
    opt_sharpe = opt_return / opt_vol if opt_vol > 0 else 0.0

    weights_df = pd.DataFrame({
        "Activo": stock_names,
        "Ponderación Óptima (w)": optimal_weights,
        "Porcentaje (%)": optimal_weights * 100.0,
    }).sort_values(by="Ponderación Óptima (w)", ascending=False).reset_index(drop=True)

    portfolio_historical_returns = stock_returns.dot(optimal_weights)

    return {
        "weights": optimal_weights,
        "weights_df": weights_df,
        "expected_return": opt_return,
        "volatility": opt_vol,
        "sharpe_ratio": opt_sharpe,
        "target_max_std": max_std,
        "is_constraint_active": abs(opt_vol - max_std) < 1e-3,
        "portfolio_returns": portfolio_historical_returns,
        "optimization_success": res.success,
    }


def optimize_minimum_variance(stock_returns: pd.DataFrame) -> Dict[str, Any]:
    """
    Cartera de Varianza Mínima Global (Long-Only, sum(w)=1):
    Punto de anclaje inferior de la frontera eficiente.
    """
    mean_returns = stock_returns.mean().values
    cov_matrix = stock_returns.cov().values
    n = len(mean_returns)

    def portfolio_volatility(w: np.ndarray) -> float:
        return float(np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))))

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = tuple((0.0, 1.0) for _ in range(n))
    w0 = np.ones(n) / n

    res = minimize(
        portfolio_volatility,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )

    weights = res.x
    weights = np.where(weights < 1e-5, 0.0, weights)
    weights = weights / np.sum(weights)

    vol = portfolio_volatility(weights)
    ret = float(np.dot(weights, mean_returns))
    sharpe = ret / vol if vol > 0 else 0.0

    return {
        "weights": weights,
        "expected_return": ret,
        "volatility": vol,
        "sharpe_ratio": sharpe,
    }


def run_monte_carlo_simulation(
    stock_returns: pd.DataFrame,
    num_portfolios: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Simulación de Monte Carlo:
    - Genera 1,000 carteras aleatorias en el símplex (sum(w)=1, w>=0).
    - Calcula rendimiento mensual, riesgo mensual (sigma_p) y Sharpe mensual (Rf=0).
    """
    np.random.seed(seed)
    mean_returns = stock_returns.mean().values
    cov_matrix = stock_returns.cov().values
    n = len(mean_returns)

    returns_sim = np.zeros(num_portfolios)
    volatilities_sim = np.zeros(num_portfolios)
    sharpes_sim = np.zeros(num_portfolios)
    all_weights = np.zeros((num_portfolios, n))

    for i in range(num_portfolios):
        w = np.random.exponential(scale=1.0, size=n)
        w = w / np.sum(w)
        all_weights[i, :] = w

        ret = np.dot(w, mean_returns)
        vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
        sharpe = ret / vol if vol > 0 else 0.0

        returns_sim[i] = ret
        volatilities_sim[i] = vol
        sharpes_sim[i] = sharpe

    max_sharpe_idx = int(np.argmax(sharpes_sim))
    min_vol_idx = int(np.argmin(volatilities_sim))

    sim_df = pd.DataFrame({
        "Rendimiento Mensual": returns_sim,
        "Volatilidad Mensual": volatilities_sim,
        "Ratio Sharpe Mensual": sharpes_sim,
    })

    return {
        "simulation_df": sim_df,
        "all_weights": all_weights,
        "max_sharpe_portfolio": {
            "index": max_sharpe_idx,
            "return": returns_sim[max_sharpe_idx],
            "volatility": volatilities_sim[max_sharpe_idx],
            "sharpe": sharpes_sim[max_sharpe_idx],
            "weights": all_weights[max_sharpe_idx],
        },
        "min_vol_portfolio": {
            "index": min_vol_idx,
            "return": returns_sim[min_vol_idx],
            "volatility": volatilities_sim[min_vol_idx],
            "sharpe": sharpes_sim[min_vol_idx],
            "weights": all_weights[min_vol_idx],
        },
    }


def calculate_benchmark_metrics(
    portfolio_returns: pd.Series,
    ipc_returns: Optional[pd.Series],
) -> Optional[Dict[str, Any]]:
    """
    Calcula métricas financieras comparativas frente al índice IPC:
    - Beta de la cartera frente al IPC: Beta = Cov(Rp, Rm) / Var(Rm).
    - Alpha mensual de Jensen: Alpha = Rp - Beta * Rm.
    - Correlación de la cartera con el IPC.
    - Tracking Error y Rendimiento Acumulado.
    """
    if ipc_returns is None or len(ipc_returns) == 0:
        return None

    aligned = pd.concat([portfolio_returns.rename("Portfolio"), ipc_returns.rename("IPC")], axis=1).dropna()
    if len(aligned) < 2:
        return None

    rp = aligned["Portfolio"]
    rm = aligned["IPC"]

    cov_pm = np.cov(rp, rm)[0, 1]
    var_m = np.var(rm, ddof=1)
    beta = cov_pm / var_m if var_m > 0 else 0.0

    mean_p = rp.mean()
    mean_m = rm.mean()
    alpha_monthly = mean_p - (beta * mean_m)

    std_p = rp.std()
    std_m = rm.std()
    corr_pm = np.corrcoef(rp, rm)[0, 1]

    diff = rp - rm
    tracking_error = diff.std()

    cum_p = (1.0 + rp).prod() - 1.0
    cum_m = (1.0 + rm).prod() - 1.0

    return {
        "ipc_mean_monthly": mean_m,
        "ipc_std_monthly": std_m,
        "ipc_sharpe_monthly": mean_m / std_m if std_m > 0 else 0.0,
        "portfolio_beta": beta,
        "portfolio_alpha_monthly": alpha_monthly,
        "correlation_with_ipc": corr_pm,
        "tracking_error_monthly": tracking_error,
        "cumulative_portfolio_return": cum_p,
        "cumulative_ipc_return": cum_m,
        "aligned_series": aligned,
    }
