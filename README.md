# 📈 Plataforma Cuantitativa Markowitz con Agente IA Autónomo

> **Maestría en Dirección Financiera e Inteligencia Artificial MBA**  
> *Materia: Financial Management with Artificial Intelligence*

Una plataforma interactiva, moderna y lista para producción diseñada para aplicar la **Teoría Moderna de Carteras de Harry Markowitz**, ejecutar **Simulaciones de Monte Carlo (1,000 carteras)**, desplegar un **Agente Cuantitativo Financiero Autónomo**, y exportar informes ejecutivos en formato **Word (.docx)** y cuadernos listos para **Google Colab**.

---

## 🎯 Reglas Metodológicas Estrictas Cumplidas

1. **Preprocesamiento y Regla del Tiempo Crítica**:
   - Detección automática del orden cronológico. Si el archivo viene ordenado de la fecha más reciente (arriba) a la más antigua (abajo), el sistema **invierte el orden** para que el dato más antiguo quede en la primera fila (estricto pasado $\to$ presente antes de cualquier cálculo).
   - Cálculo de rendimientos simples mensuales: $R_t = \frac{P_t - P_{t-1}}{P_{t-1}}$.
   - **Exclusión estricta del IPC** de las ponderaciones de la cartera (se reserva como benchmark de mercado para Alpha y Beta).
   - Depuración de nulos (NaN) y filtrado de filas residuales.
2. **Parámetros Estadísticos (Estrictamente Mensuales)**:
   - Medias aritméticas mensuales de rendimientos ($\mu_i$).
   - Matriz de covarianza mensual ($\Sigma$) y matriz de correlación.
   - 🚨 **PROHIBICIÓN ABSOLUTA DE ANUALIZACIÓN**: Ningún cálculo matemático multiplica por 12 ni por $\sqrt{12}$. Todo el análisis permanece en frecuencia mensual.
3. **Optimización de la Cartera (Frontera Eficiente)**:
   - **Función Objetivo**: Maximizar el rendimiento mensual esperado de la cartera ($\max_w w^T \mu$).
   - **Restricción 1**: Desviación estándar mensual de la cartera acotada a $\sigma_p \le 0.07$ (7.00% mensual).
   - **Restricción 2**: 100% del capital invertido ($\sum w_i = 1$).
   - **Límites**: Solo posiciones largas ($w_i \ge 0$, sin ventas en corto).
   - Resuelto mediante programación no lineal convexa SLSQP (`scipy.optimize.minimize`).
4. **Simulación de Monte Carlo (1,000 Carteras)**:
   - Muestreo Dirichlet de 1,000 combinaciones aleatorias en el símplex ($\sum w_i = 1, w_i \ge 0$).
   - Rendimiento, riesgo y Ratio de Sharpe mensual (con tasa libre de riesgo $R_f = 0$).
   - Graficación interactiva de la nube de dispersión de la frontera eficiente.
5. **Agente Financiero Cuantitativo Autónomo**:
   - Diagnósticos automáticos de calidad de datos, perfil individual de activos, sinergias de covarianza, justificación de pesos del portafolio óptimo y comparación contra el IPC.
   - Motor 100% autónomo y offline, con soporte opcional para conectar modelos LLM vía API key (Gemini/OpenAI).
6. **Entregables en Producción**:
   - Generación instantánea de informe en **Word (.docx)** con tablas estilizadas y gráficos en alta resolución.
   - Script Python (`markowitz_colab.py`) y Cuaderno Jupyter (`markowitz_colab.ipynb`) compatibles con **Google Colab**.

---

## 📁 Estructura del Proyecto

```
proyecto/
├── app.py                     # Plataforma interactiva Streamlit con visualizador de progreso
├── optimizer.py               # Motor de cálculo cuantitativo estricto y Markowitz
├── agent.py                   # Agente Cuantitativo Autónomo (lógica financiera e IA)
├── word_exporter.py           # Generador de informes ejecutivos en Word (.docx)
├── markowitz_colab.py         # Script Python standalone para Google Colab o terminal
├── markowitz_colab.ipynb      # Cuaderno interactivo Jupyter para Google Colab
├── test_pipeline.py           # Suite de pruebas unitarias automatizadas
├── Histórico_Acciones.xlsx     # Archivo histórico base provisto en el proyecto
├── requirements.txt           # Dependencias de Python
├── Dockerfile                 # Contenedor para despliegue en la nube
└── README.md                  # Documentación del proyecto
```

---

## 🚀 Cómo Ejecutar la Plataforma

### Opción 1: Ejecución Local

1. Clona o abre la carpeta del proyecto en tu terminal.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicia la aplicación interactiva:
   ```bash
   streamlit run app.py
   ```
4. Abre tu navegador en `http://localhost:8501`.

---

### Opción 2: Ejecución en Google Colab

1. Abre [Google Colab](https://colab.research.google.com/).
2. Sube el archivo `markowitz_colab.ipynb` o `markowitz_colab.py`.
3. Ejecuta las celdas. Se te solicitará subir el archivo Excel (o usará el archivo si ya está en la sesión).
4. El script generará los gráficos y descargará automáticamente el informe Word `Informe_Markowitz_Colab.docx`.

---

### Opción 3: Despliegue en Producción con Docker

1. Construir la imagen del contenedor:
   ```bash
   docker build -t markowitz-platform .
   ```
2. Ejecutar el contenedor en el puerto 8501:
   ```bash
   docker run -d -p 8501:8501 --name markowitz-app markowitz-platform
   ```
3. Acceder en `http://localhost:8501`.

---

### Opción 4: Despliegue Gratuito en Streamlit Community Cloud / Render

1. Sube este repositorio a **GitHub**.
2. Entra a [Streamlit Community Cloud](https://share.streamlit.io/).
3. Selecciona tu repositorio y define el archivo principal como `app.py`.
4. ¡Tu plataforma estará pública en producción en menos de 2 minutos!

---

## 🧪 Verificación y Pruebas Automatizadas

Para validar que todas las reglas estrictas se cumplen:

```bash
python3 test_pipeline.py
```

Salida esperada:
```
Ran 7 tests in ~1s
OK
```
