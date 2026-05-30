import os
import subprocess
import sys
import time


def main():
    print("🚀 Iniciando SEM Express - Orquestador Local...")
    print("===============================================")

    try:
        print("Levantando API (FastAPI)...")
        api = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"])
        time.sleep(3)

        print("Levantando Dashboard (Streamlit)...")
        env = os.environ.copy()
        env["API_URL"] = "http://127.0.0.1:8000"
        dashboard = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.port", "8501"],
            env=env,
        )

        print("Levantando Bot de Telegram...")
        bot = subprocess.Popen([sys.executable, "bot_telegram.py"])

        print("\n✅ Todos los servicios estan corriendo en paralelo!")
        print("👉 API: http://127.0.0.1:8000/docs")
        print("👉 Dashboard: http://localhost:8501")
        print("Presiona Ctrl+C para apagar todo.\n")

        api.wait()
        dashboard.wait()
        bot.wait()

    except KeyboardInterrupt:
        print("\n🛑 Apagando servicios...")
        api.terminate()
        dashboard.terminate()
        bot.terminate()


if __name__ == "__main__":
    main()
