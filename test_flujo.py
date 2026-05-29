import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "")


def _headers():
    h = {}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def ejecutar_prueba():
    try:
        print("Simulando llegada de vehiculo...")
        payload_inicio = {"patente": "TEST99", "tipo_vehiculo": "auto", "legajo_permisionario": "PERM-TEST"}
        response_inicio = requests.post(f"{API_URL}/v1/estacionamiento/iniciar", json=payload_inicio, headers=_headers())
        print(f"Status: {response_inicio.status_code}")
        print(response_inicio.json())
        print("-" * 50)

        print("Pausando 2 segundos...")
        time.sleep(2)

        print("Simulando pago...")
        payload_cobro = {"patente": "TEST99", "metodo_pago": "digital"}
        response_cobro = requests.post(f"{API_URL}/v1/estacionamiento/cobrar", json=payload_cobro, headers=_headers())
        print(f"Status: {response_cobro.status_code}")
        print(response_cobro.json())
        print("-" * 50)
        print("Flujo completo exitoso.")

    except requests.exceptions.ConnectionError:
        print("Error: API no esta corriendo. Ejecuta: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    ejecutar_prueba()
