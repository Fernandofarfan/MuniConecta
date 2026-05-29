import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "")


def _headers():
    if API_KEY:
        return {"X-API-Key": API_KEY}
    return {}


def ejecutar_prueba():
    try:
        print("Simulando llegada de vehiculo...")

        payload_inicio = {
            "patente": "TEST99",
            "tipo_vehiculo": "auto",
            "legajo_permisionario": "PERM-TEST",
        }

        response_inicio = requests.post(
            f"{API_BASE_URL}/iniciar_estacionamiento",
            json=payload_inicio,
            headers=_headers(),
        )
        print(f"Status Code: {response_inicio.status_code}")
        print("Respuesta del Servidor:")
        print(response_inicio.json())
        print("-" * 50)

        print("Pausando ejecucion por 2 segundos...")
        time.sleep(2)

        print("Simulando pago y retiro del vehiculo...")

        payload_cobro = {"patente": "TEST99", "metodo_pago": "digital"}

        response_cobro = requests.post(
            f"{API_BASE_URL}/calcular_cobro",
            json=payload_cobro,
            headers=_headers(),
        )
        print(f"Status Code: {response_cobro.status_code}")
        print("Respuesta Final del Cobro:")
        print(response_cobro.json())
        print("-" * 50)

        print("Prueba de flujo completo finalizada con exito.")

    except requests.exceptions.ConnectionError:
        print("Error de Conexion: La API de FastAPI no esta encendida.")
        print("Asegurate de correr 'uvicorn app.main:app --reload' en otra terminal.")
    except Exception as e:
        print(f"Ocurrio un error inesperado durante la prueba: {e}")


if __name__ == "__main__":
    ejecutar_prueba()
