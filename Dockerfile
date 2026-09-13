# Imagen base oficial y liviana de Python
FROM python:3.11-slim

# Metadatos
LABEL maintainer="MBA Financial Management with AI"
LABEL description="Markowitz Portfolio Optimization & Autonomous AI Quant Agent Platform"

# Evitar escritura de bytecode y habilitar buffer directo de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema mínimas necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar archivo de requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código y archivos del proyecto
COPY . .

# Exponer el puerto estándar de Streamlit
EXPOSE 8501

# Comprobación de salud (Healthcheck)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando de ejecución
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
