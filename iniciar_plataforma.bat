@echo off
title Plataforma Cuantitativa Markowitz & Agente IA
cd /d "%~dp0"

echo ==================================================================
echo Instando / Iniciando Plataforma Cuantitativa Markowitz con Agente IA
echo ==================================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python no esta instalado o no esta agregado al PATH.
    echo Descargalo e instalalo desde https://www.python.org/
    pause
    exit /b
)

python -c "import streamlit, plotly, reportlab, yfinance" >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias en primer uso...
    python -m pip install -r requirements.txt
)

python desktop_launcher.py
pause
