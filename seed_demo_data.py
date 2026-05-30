import os
import random
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

TZ_ARG = timezone(timedelta(hours=-3))
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

PATENTES = ["AB123CD", "AAA000", "AC456DE", "BB789FG", "CC012HI", "DD345JK", "EE678LM", "FF901NP"]
LEGAJOS = ["INSP-01", "INSP-02", "INSP-03"]
ZONAS = [1, 2, 3]
METODOS = ["efectivo", "digital"]
HORAS_PICO = [9, 10, 11, 12, 17, 18, 19]

import requests


def seed():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Configura SUPABASE_URL y SUPABASE_KEY en .env")
        return

    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    url = f"{SUPABASE_URL}/rest/v1/estacionamientos"

    print("Generando 30 dias de datos de estacionamiento...")
    ahora = datetime.now(TZ_ARG)

    for dia in range(30, 0, -1):
        fecha = ahora - timedelta(days=dia)
        for _ in range(random.randint(5, 25)):
            hora = random.choice(HORAS_PICO) + random.randint(0, 3)
            inicio = fecha.replace(hour=hora, minute=random.randint(0, 59))
            duracion = random.randint(15, 240)
            fin = inicio + timedelta(minutes=duracion)
            patente = random.choice(PATENTES)
            tipo = random.choice(["auto", "moto"])
            tarifa = 700 if tipo == "auto" else 300
            metodo = random.choice(METODOS)
            monto = round(tarifa * (duracion / 60) * (0.8 if metodo == "digital" else 1.0), 2)

            carga = {
                "patente": patente,
                "tipo_vehiculo": tipo,
                "legajo_permisionario": random.choice(LEGAJOS),
                "hora_inicio": inicio.isoformat(),
                "hora_fin": fin.isoformat(),
                "estado": "finalizado",
                "monto_final": monto,
                "metodo_pago": metodo,
                "zona_id": random.choice(ZONAS),
                "lat": -24.7883 + random.uniform(-0.01, 0.01),
                "lon": -65.4105 + random.uniform(-0.01, 0.01),
            }

            try:
                r = requests.post(url, headers=headers, json=carga, timeout=5)
                if r.status_code not in (201, 204):
                    print(f"  Error dia {dia}: {r.status_code}")
            except Exception as e:
                print(f"  Error: {e}")

        if dia % 5 == 0:
            print(f"  Dia {30-dia}/30 completado")

    # Crear algunas sesiones activas
    print("Creando sesiones activas...")
    for i in range(random.randint(5, 10)):
        carga = {
            "patente": random.choice(PATENTES),
            "tipo_vehiculo": random.choice(["auto", "moto"]),
            "legajo_permisionario": random.choice(LEGAJOS),
            "hora_inicio": ahora.isoformat(),
            "estado": "activo",
            "zona_id": random.choice(ZONAS),
            "lat": -24.7883 + random.uniform(-0.01, 0.01),
            "lon": -65.4105 + random.uniform(-0.01, 0.01),
        }
        try:
            requests.post(url, headers=headers, json=carga, timeout=5)
        except Exception:
            pass

    print("Datos de demostracion generados!")
    print("Ver dashboard: http://localhost:8501")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    seed()
