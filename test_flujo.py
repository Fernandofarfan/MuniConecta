import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def ejecutar_prueba():
    try:
        print("🚗 Simulando llegada de vehículo...")
        
        # 1. Iniciar el estacionamiento
        payload_inicio = {
            "patente": "TEST999",
            "tipo_vehiculo": "auto",
            "legajo_permisionario": "PERM-TEST"
        }
        
        response_inicio = requests.post(f"{API_BASE_URL}/iniciar_estacionamiento", json=payload_inicio)
        print(f"Status Code: {response_inicio.status_code}")
        print("Respuesta del Servidor:")
        print(response_inicio.json())
        print("-" * 50)
        
        # 2. Esperar 2 segundos
        print("⏱️ Pausando ejecución por 2 segundos...")
        time.sleep(2)
        
        # 3. Finalizar el estacionamiento y cobrar
        print("💳 Simulando pago y retiro del vehículo...")
        
        payload_cobro = {
            "patente": "TEST999",
            "metodo_pago": "digital"
        }
        
        response_cobro = requests.post(f"{API_BASE_URL}/calcular_cobro", json=payload_cobro)
        print(f"Status Code: {response_cobro.status_code}")
        print("Respuesta Final del Cobro:")
        print(response_cobro.json())
        print("-" * 50)
        
        print("✅ Prueba de flujo completo finalizada con éxito.")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error de Conexión: La API de FastAPI no está encendida.")
        print("Por favor, asegúrate de correr 'fastapi dev main.py' o 'uvicorn main:app --reload' en otra terminal antes de ejecutar este script.")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado durante la prueba: {e}")

if __name__ == "__main__":
    ejecutar_prueba()
