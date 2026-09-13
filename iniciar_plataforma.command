#!/bin/bash
# Script de Doble Clic para macOS / Linux
cd "$(dirname "$0")"

echo "=================================================================="
echo "🚀 Iniciando Plataforma Cuantitativa Markowitz con Agente IA"
echo "=================================================================="

# Verificar Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python no se encuentra instalado en este equipo."
    echo "Por favor instala Python 3.10 o superior desde https://www.python.org/"
    read -p "Presiona Enter para salir..."
    exit 1
fi

# Instalar dependencias si no existen
$PYTHON_CMD -c "import streamlit, plotly, reportlab, yfinance" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Instalando paquetes requeridos en primer inicio..."
    $PYTHON_CMD -m pip install -r requirements.txt
fi

# Iniciar lanzador
$PYTHON_CMD desktop_launcher.py
