"""
Generador de Informes Ejecutivos en PDF con ReportLab
Produce un documento de nivel institucional con:
- Portada ejecutiva y formato corporativo.
- Tablas estilizadas con parámetros estrictamente mensuales.
- Gráficos incrustados en alta resolución.
- Dictamen y análisis profundo del Agente Cuantitativo Financiero Autónomo.
- Log de auditoría y depuración de errores del archivo.
"""

from typing import Dict, Any, Optional
import io
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    HRFlowable,
    PageBreak,
)


def create_charts_temp_files(
    stats_data: Dict[str, Any],
    opt_data: Dict[str, Any],
    mc_data: Dict[str, Any],
    bench_data: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    """Genera imágenes temporales en alta resolución para incrustar en el PDF."""
    chart_paths = {}
    sns.set_theme(style="whitegrid")

    # 1. Gráfico Monte Carlo
    fig1, ax1 = plt.subplots(figsize=(8.0, 4.2), dpi=250)
    sim_df = mc_data["simulation_df"]
    sc = ax1.scatter(
        sim_df["Volatilidad Mensual"] * 100,
        sim_df["Rendimiento Mensual"] * 100,
        c=sim_df["Ratio Sharpe Mensual"],
        cmap="viridis",
        alpha=0.65,
        s=18,
    )
    cbar = plt.colorbar(sc, ax=ax1)
    cbar.set_label("Sharpe Mensual (Rf=0)", fontsize=8)

    opt_vol = opt_data["volatility"] * 100
    opt_ret = opt_data["expected_return"] * 100
    ax1.scatter([opt_vol], [opt_ret], color="#EF4444", s=160, marker="*", label=f"Cartera Óptima (Ret: {opt_ret:.2f}%, Vol: {opt_vol:.2f}%)", zorder=5)
    ax1.axvline(x=opt_data["target_max_std"] * 100, color="#DC2626", linestyle="--", label=f"Tope Riesgo (≤ {opt_data['target_max_std']*100:.1f}%)")

    if bench_data:
        ipc_vol = bench_data["ipc_std_monthly"] * 100
        ipc_ret = bench_data["ipc_mean_monthly"] * 100
        ax1.scatter([ipc_vol], [ipc_ret], color="#10B981", s=110, marker="D", label=f"Benchmark IPC (Ret: {ipc_ret:.2f}%, Vol: {ipc_vol:.2f}%)", zorder=4)

    ax1.set_title("Nube de Monte Carlo & Cartera Óptima de Markowitz (Datos Mensuales)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Volatilidad Mensual σ_p (%) [PROHIBIDO ANUALIZAR]", fontsize=9)
    ax1.set_ylabel("Rendimiento Esperado Mensual μ_p (%)", fontsize=9)
    ax1.legend(loc="upper left", fontsize=8)
    plt.tight_layout()
    p1 = "temp_pdf_chart_mc.png"
    plt.savefig(p1, bbox_inches="tight")
    plt.close(fig1)
    chart_paths["mc"] = p1

    # 2. Gráfico de Ponderaciones
    fig2, ax2 = plt.subplots(figsize=(7.5, 3.6), dpi=250)
    w_df = opt_data["weights_df"]
    w_act = w_df[w_df["Ponderación Óptima (w)"] > 0.001].copy()
    colors_list = sns.color_palette("Blues_r", n_colors=len(w_act))
    bars = ax2.barh(w_act["Activo"], w_act["Porcentaje (%)"], color=colors_list, height=0.55)
    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 0.6, bar.get_y() + bar.get_height() / 2, f"{w:.2f}%", va="center", fontsize=9, fontweight="bold")
    ax2.set_xlim(0, max(w_act["Porcentaje (%)"]) * 1.18)
    ax2.invert_yaxis()
    ax2.set_title("Asignación Óptima de Capital (Markowitz Long-Only)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Ponderación en Portafolio (%)", fontsize=9)
    plt.tight_layout()
    p2 = "temp_pdf_chart_weights.png"
    plt.savefig(p2, bbox_inches="tight")
    plt.close(fig2)
    chart_paths["weights"] = p2

    # 3. Matriz de Correlación
    fig3, ax3 = plt.subplots(figsize=(7.0, 5.0), dpi=250)
    sns.heatmap(stats_data["corr_matrix"], annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax3, annot_kws={"size": 7})
    ax3.set_title("Matriz de Correlación de Rendimientos Mensuales", fontsize=11, fontweight="bold")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    p3 = "temp_pdf_chart_corr.png"
    plt.savefig(p3, bbox_inches="tight")
    plt.close(fig3)
    chart_paths["corr"] = p3

    return chart_paths


def generate_pdf_report(
    prep_data: Dict[str, Any],
    stats_data: Dict[str, Any],
    opt_data: Dict[str, Any],
    mc_data: Dict[str, Any],
    bench_data: Optional[Dict[str, Any]],
    agent_report: Dict[str, Any],
    output_path: Optional[str] = None,
) -> io.BytesIO:
    """Genera un archivo PDF ejecutivo completo."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )

    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    style_title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    style_sub = ParagraphStyle(
        "ReportSub",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#475569"),
        fontName="Helvetica-Oblique",
        spaceAfter=12,
    )
    style_h2 = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0369a1"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=6,
    )
    style_body = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica",
        spaceAfter=6,
    )
    style_table_header = ParagraphStyle(
        "TableHdr",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.white,
        alignment=1,
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica",
        alignment=0,
    )
    style_table_cell_right = ParagraphStyle(
        "TableCellR",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica",
        alignment=2,
    )

    style_cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
        alignment=1,
    )
    style_cover_sub = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontSize=14,
        leading=19,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
        alignment=1,
    )
    style_cover_label = ParagraphStyle(
        "CoverLabel",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        fontName="Helvetica",
        alignment=1,
    )
    style_cover_val = ParagraphStyle(
        "CoverVal",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
        alignment=1,
    )
    style_cover_univ = ParagraphStyle(
        "CoverUniv",
        parent=styles["Normal"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
        alignment=1,
    )
    style_cover_mba = ParagraphStyle(
        "CoverMba",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#334155"),
        fontName="Helvetica",
        alignment=1,
    )
    style_cover_date = ParagraphStyle(
        "CoverDate",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        fontName="Helvetica",
        alignment=1,
    )

    story = []

    # ----------------------------------------------------
    # PORTADA ACADÉMICA OFICIAL (portada.docx)
    # ----------------------------------------------------
    story.append(Spacer(1, 0.4 * inch))
    logo_path = os.path.join("assets", "logo_universidad.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join("assets", "logo_universidad.jpg")

    if os.path.exists(logo_path):
        img = Image(logo_path, width=2.2 * inch, height=1.47 * inch)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 0.45 * inch))

    story.append(Paragraph("TRABAJO", style_cover_title))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Portafolio diversificado usando rendimientos reales", style_cover_sub))
    story.append(Spacer(1, 0.55 * inch))

    story.append(Paragraph("Presentan:", style_cover_label))
    story.append(Spacer(1, 0.06 * inch))
    story.append(Paragraph("Cristian Andres Cordoba Gonzalez (Colombia)", style_cover_val))
    story.append(Spacer(1, 0.45 * inch))

    story.append(Paragraph("Profesor:", style_cover_label))
    story.append(Spacer(1, 0.06 * inch))
    story.append(Paragraph("Daniel Vázquez Cotera", style_cover_val))
    story.append(Spacer(1, 0.65 * inch))

    story.append(Paragraph("Broward International University", style_cover_univ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Financial Management with Artificial Intelligence MBA", style_cover_mba))
    story.append(Spacer(1, 0.55 * inch))

    story.append(Paragraph("13 de septiembre de 2026", style_cover_date))
    story.append(PageBreak())

    # 1. Encabezado
    story.append(Paragraph("INFORME EJECUTIVO CUANTITATIVO DE CARTERAS", style_title))
    story.append(Paragraph("Teoría de Harry Markowitz & Simulación de Monte Carlo (Cálculos Estrictamente Mensuales)", style_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=10))

    # 2. Metadatos
    start_str = prep_data["start_date"].strftime("%b %Y") if hasattr(prep_data["start_date"], "strftime") else str(prep_data["start_date"])
    end_str = prep_data["end_date"].strftime("%b %Y") if hasattr(prep_data["end_date"], "strftime") else str(prep_data["end_date"])
    
    meta_data = [
        [
            Paragraph(f"<b>Período Analizado:</b> {start_str} - {end_str}", style_body),
            Paragraph(f"<b>Observaciones:</b> {prep_data['num_periods']} meses", style_body),
        ],
        [
            Paragraph(f"<b>Universo de Activos:</b> {len(prep_data['stock_cols'])} Acciones BMV", style_body),
            Paragraph(f"<b>Restricción de Riesgo:</b> σ_p ≤ {opt_data['target_max_std']:.1%} mensual", style_body),
        ],
        [
            Paragraph(f"<b>Benchmark:</b> {prep_data.get('ipc_col', 'IPC')} (Excluido de pesos)", style_body),
            Paragraph("<b>Agente:</b> Cuantitativo Autónomo MBA", style_body),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[3.5 * inch, 3.5 * inch])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # 3. Resumen Ejecutivo
    story.append(Paragraph("1. Resumen Ejecutivo y Hallazgos Clave", style_h2))
    story.append(Paragraph(agent_report["executive_summary"], style_body))
    story.append(Spacer(1, 6))

    # 4. Tabla de Auditoría de Calidad y Depuración
    story.append(Paragraph("2. Auditoría de Calidad de Datos & Limpieza del Archivo", style_h2))
    audit_events = prep_data.get("audit_events", [])
    t_audit_data = [[
        Paragraph("Etapa", style_table_header),
        Paragraph("Detalle de la Detección / Corrección", style_table_header),
        Paragraph("Severidad", style_table_header),
        Paragraph("Acción Cuantitativa", style_table_header),
    ]]
    for ev in audit_events[:6]:
        t_audit_data.append([
            Paragraph(str(ev.get("Etapa", "")), style_table_cell),
            Paragraph(str(ev.get("Detalle", "")), style_table_cell),
            Paragraph(str(ev.get("Severidad", "")), style_table_cell),
            Paragraph(str(ev.get("Acción", "")), style_table_cell),
        ])
    t_audit = Table(t_audit_data, colWidths=[1.3 * inch, 3.2 * inch, 1.0 * inch, 1.5 * inch])
    t_audit.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_audit)
    story.append(Spacer(1, 10))

    # 5. Parámetros Estadísticos Mensuales
    story.append(Paragraph("3. Parámetros Estadísticos Mensuales (Estricto: Sin Anualizar)", style_h2))
    stats_df = stats_data["stats_table"]
    t_stats_data = [[
        Paragraph("Activo", style_table_header),
        Paragraph("Retorno Mensual", style_table_header),
        Paragraph("Volatilidad Mensual", style_table_header),
        Paragraph("Varianza Mensual", style_table_header),
        Paragraph("Sharpe (Rf=0)", style_table_header),
    ]]
    for asset, row in stats_df.iterrows():
        t_stats_data.append([
            Paragraph(f"<b>{asset}</b>", style_table_cell),
            Paragraph(f"{row['Rendimiento Mensual Promedio']*100:.2f}%", style_table_cell_right),
            Paragraph(f"{row['Volatilidad Mensual (Desv. Est.)']*100:.2f}%", style_table_cell_right),
            Paragraph(f"{row['Varianza Mensual']:.5f}", style_table_cell_right),
            Paragraph(f"{row['Ratio Sharpe Mensual (Rf=0)']:.4f}", style_table_cell_right),
        ])
    t_stats = Table(t_stats_data, colWidths=[1.8 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch])
    t_stats.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_stats)
    story.append(Spacer(1, 10))

    # 6. Cartera Óptima de Markowitz
    story.append(Paragraph(f"4. Cartera Óptima de Markowitz (σ_p ≤ {opt_data['target_max_std']*100:.2f}% Mensual)", style_h2))
    story.append(Paragraph(
        f"• <b>Rendimiento Esperado Mensual (μ_p):</b> {opt_data['expected_return']*100:.3f}%<br/>"
        f"• <b>Volatilidad Mensual (σ_p):</b> {opt_data['volatility']*100:.3f}% (Restricción ≤ {opt_data['target_max_std']*100:.2f}% satisfecha)<br/>"
        f"• <b>Ratio de Sharpe Mensual:</b> {opt_data['sharpe_ratio']:.4f}",
        style_body
    ))
    
    weights_df = opt_data["weights_df"]
    t_w_data = [[
        Paragraph("Activo", style_table_header),
        Paragraph("Ponderación Decimal (w_i)", style_table_header),
        Paragraph("Asignación Porcentual (%)", style_table_header),
    ]]
    for _, row in weights_df.iterrows():
        t_w_data.append([
            Paragraph(str(row["Activo"]), style_table_cell),
            Paragraph(f"{row['Ponderación Óptima (w)']:.4f}", style_table_cell_right),
            Paragraph(f"<b>{row['Porcentaje (%)']:.2f}%</b>" if row["Porcentaje (%)"] > 0.01 else f"{row['Porcentaje (%)']:.2f}%", style_table_cell_right),
        ])
    t_w = Table(t_w_data, colWidths=[2.6 * inch, 2.2 * inch, 2.2 * inch])
    t_w.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_w)
    story.append(Spacer(1, 10))

    # 7. Gráficos Incrustados
    chart_paths = create_charts_temp_files(stats_data, opt_data, mc_data, bench_data)
    
    story.append(Paragraph("5. Visualizaciones Cuantitativas", style_h2))
    story.append(Image(chart_paths["mc"], width=6.8 * inch, height=3.5 * inch))
    story.append(Spacer(1, 8))
    story.append(Image(chart_paths["weights"], width=6.8 * inch, height=3.2 * inch))
    story.append(Spacer(1, 8))
    story.append(Image(chart_paths["corr"], width=6.5 * inch, height=4.6 * inch))
    story.append(Spacer(1, 10))

    # 8. Evaluación vs Benchmark
    if bench_data:
        story.append(Paragraph("6. Desempeño Comparativo frente al Benchmark (IPC)", style_h2))
        story.append(Paragraph(agent_report["bench_insights"]["text"].replace("\n", "<br/>"), style_body))
        story.append(Spacer(1, 8))

    # 9. Dictamen del Agente Cuantitativo
    story.append(Paragraph("7. Dictamen del Agente Cuantitativo Financiero Autónomo", style_h2))
    story.append(Paragraph(agent_report["opt_insights"]["text"].replace("\n", "<br/>"), style_body))
    story.append(Spacer(1, 6))
    story.append(Paragraph(agent_report["mc_insights"]["text"].replace("\n", "<br/>"), style_body))
    story.append(Spacer(1, 6))
    story.append(Paragraph(agent_report["recommendations"].replace("\n", "<br/>"), style_body))

    # Construir PDF
    doc.build(story)
    buf.seek(0)

    # Limpiar imágenes temporales
    for p in chart_paths.values():
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    if output_path:
        with open(output_path, "wb") as f:
            f.write(buf.getvalue())

    return buf
