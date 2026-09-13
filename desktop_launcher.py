"""
Lanzador de Escritorio Portátil para la Plataforma Markowitz
Abre automáticamente la plataforma en el navegador web predeterminado del sistema.
Compatible con Windows, macOS y Linux.
"""

import os
import sys
import time
import webbrowser
import subprocess

def launch_app():
    port = 8501
    url = f"http://localhost:{port}"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")

    print("=" * 70)
    print("📈 INICIANDO PLATAFORMA CUANTITATIVA MARKOWITZ & AGENTE IA")
    print("=" * 70)
    print(f"Directorio de ejecución: {script_dir}")
    print(f"Abriendo plataforma en navegador web: {url}")
    print("Para salir o cerrar la aplicación, presiona Ctrl + C en esta ventana.\n")

    # Iniciar subproceso de Streamlit
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        app_path,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]

    # Abrir navegador tras 2 segundos
    def open_browser():
        time.sleep(2.0)
        webbrowser.open_new(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Ejecutar proceso principal
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nCerrando la plataforma de manera segura. ¡Hasta pronto!")

if __name__ == "__main__":
    launch_app()
