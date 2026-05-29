import os
import subprocess
import sys
import time


def main():
    print("🚀 Iniciando SEM Express - Orquestador Local...")
    print("===============================================")

    try:
        # 1. Iniciar FastAPI
        print("Levantando Backend (FastAPI)...")
        api = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"])
        time.sleep(3) # Damos tiempo a que levante el puerto

        # 2. Iniciar Dashboard de Streamlit
        print("Levantando Dashboard (Streamlit)...")
        env = os.environ.copy()
        env["API_URL"] = "http://127.0.0.1:8000"
        dashboard = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.port", "8501"], env=env)

        # 3. Iniciar Bot de Telegram
        print("Levantando Bot de Telegram...")
        bot = subprocess.Popen([sys.executable, "bot_telegram.py"])

        print("\n✅ ¡Todos los servicios están corriendo en paralelo!")
        print("👉 API: http://127.0.0.1:8000/docs")
        print("👉 PWA Inspector: http://127.0.0.1:8000/inspector/")
        print("👉 Dashboard: http://localhost:8501")
        print("Presiona Ctrl+C para apagar todo.\n")

        api.wait()
        dashboard.wait()
        bot.wait()

    except KeyboardInterrupt:
        print("\n🛑 Señal de apagado recibida (Ctrl+C). Deteniendo servicios...")
        api.terminate()
        dashboard.terminate()
        bot.terminate()
        print("👋 Servicios detenidos exitosamente. ¡Nos vemos!")

if __name__ == "__main__":
    main()
