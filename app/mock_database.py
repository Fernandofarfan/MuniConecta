import math
import random
import time
from datetime import datetime, timedelta, timezone

TZ_ARG = timezone(timedelta(hours=-3))

_in_memory_db = {
    "estacionamientos": [],
    "infracciones": [],
    "inspectores": [
        {"id": 1, "legajo": "INSP-01", "nombre": "Carlos", "rol": "admin", "activo": True, "saldo_adeudado": 0, "password_hash": "$2b$12$hash", "zona_asignada_id": 1},
        {"id": 2, "legajo": "INSP-02", "nombre": "Maria", "rol": "inspector", "activo": True, "saldo_adeudado": 500, "password_hash": "$2b$12$hash", "zona_asignada_id": 2},
    ],
    "zonas": [
        {"id": 1, "nombre": "Microcentro", "tarifa_auto": 700, "tarifa_moto": 300, "capacidad_maxima": 100, "activa": True, "centro_lat": -24.7883, "centro_lon": -65.4105},
        {"id": 2, "nombre": "Zona Norte", "tarifa_auto": 500, "tarifa_moto": 200, "capacidad_maxima": 80, "activa": True, "centro_lat": -24.7700, "centro_lon": -65.4000},
        {"id": 3, "nombre": "Zona Sur", "tarifa_auto": 450, "tarifa_moto": 180, "capacidad_maxima": 60, "activa": True, "centro_lat": -24.8000, "centro_lon": -65.4200},
    ],
    "ciudadanos": [],
    "abonos": [],
    "auditoria": [],
    "vehiculos_saldos": {},
    "vehiculos_saldos_lista": [],
    "suscriptores_digest": [],
    "lista_espera": [],
    "anomalias": [],
    "tarifas_especiales": [],
    "comprobantes": [],
    "cierre_diario_log": [],
}
_next_id = {"estacionamientos": 1, "infracciones": 1, "auditoria": 1, "abonos": 1, "anomalias": 1}


def _now():
    return datetime.now(TZ_ARG).isoformat()


def _seed_demo_data():
    if _in_memory_db["estacionamientos"]:
        return

    ahora = datetime.now(TZ_ARG)
    patentes = ["AB123CD", "AAA000", "AC456DE", "BB789FG", "CC012HI", "DD345JK"]
    legajos = ["INSP-01", "INSP-02"]
    zonas = [1, 2, 3]
    metodos = ["efectivo", "digital"]

    for dia in range(15, 0, -1):
        fecha = ahora - timedelta(days=dia)
        for _ in range(random.randint(3, 12)):
            hora = random.choice([9, 10, 11, 12, 17, 18, 19])
            inicio = fecha.replace(hour=hora, minute=random.randint(0, 59))
            duracion = random.randint(15, 180)
            fin = inicio + timedelta(minutes=duracion)
            tipo = random.choice(["auto", "moto"])
            tarifa = 700 if tipo == "auto" else 300
            metodo = random.choice(metodos)
            monto = round(tarifa * (duracion / 60) * (0.8 if metodo == "digital" else 1.0), 2)

            _in_memory_db["estacionamientos"].append({
                "id": _next_id["estacionamientos"],
                "patente": random.choice(patentes),
                "tipo_vehiculo": tipo,
                "legajo_permisionario": random.choice(legajos),
                "hora_inicio": inicio.isoformat(),
                "hora_fin": fin.isoformat(),
                "estado": "finalizado",
                "monto_final": monto,
                "metodo_pago": metodo,
                "zona_id": random.choice(zonas),
                "lat": -24.7883 + random.uniform(-0.01, 0.01),
                "lon": -65.4105 + random.uniform(-0.01, 0.01),
            })
            _next_id["estacionamientos"] += 1

    for i in range(random.randint(3, 6)):
        _in_memory_db["estacionamientos"].append({
            "id": _next_id["estacionamientos"],
            "patente": random.choice(patentes),
            "tipo_vehiculo": random.choice(["auto", "moto"]),
            "legajo_permisionario": random.choice(legajos),
            "hora_inicio": ahora.isoformat(),
            "hora_fin": None,
            "estado": "activo",
            "monto_final": 0,
            "metodo_pago": None,
            "zona_id": random.choice(zonas),
            "lat": -24.7883 + random.uniform(-0.01, 0.01),
            "lon": -65.4105 + random.uniform(-0.01, 0.01),
        })
        _next_id["estacionamientos"] += 1


class MockDB:
    @staticmethod
    def _find(table, key, value):
        return [r for r in _in_memory_db[table] if r.get(key) == value]

    @staticmethod
    def _find_one(table, key, value):
        results = MockDB._find(table, key, value)
        return results[0] if results else None

    @staticmethod
    def get_estacionamientos():
        _seed_demo_data()
        return _in_memory_db["estacionamientos"]

    @staticmethod
    def get_infracciones():
        return _in_memory_db["infracciones"]

    @staticmethod
    def get_zonas():
        return [z for z in _in_memory_db["zonas"] if z["activa"]]

    @staticmethod
    def get_zonas_ocupacion():
        result = []
        for z in _in_memory_db["zonas"]:
            if z["activa"]:
                ocupados = len([e for e in _in_memory_db["estacionamientos"] if e.get("zona_id") == z["id"] and e["estado"] == "activo"])
                result.append({**z, "ocupados": ocupados})
        return result

    @staticmethod
    def buscar_activo_por_patente(patente):
        results = [e for e in _in_memory_db["estacionamientos"] if e["patente"] == patente and e["estado"] == "activo"]
        return results[0] if results else None

    @staticmethod
    def crear_estacionamiento(data):
        data["id"] = _next_id["estacionamientos"]
        _next_id["estacionamientos"] += 1
        _in_memory_db["estacionamientos"].append(data)

    @staticmethod
    def actualizar_activo(patente, data):
        for e in _in_memory_db["estacionamientos"]:
            if e["patente"] == patente and e["estado"] == "activo":
                e.update(data)
                break

    @staticmethod
    def obtener_activos():
        return [e for e in _in_memory_db["estacionamientos"] if e["estado"] == "activo"]

    @staticmethod
    def obtener_analiticas(desde, hasta):
        return [e for e in _in_memory_db["estacionamientos"] if desde <= e.get("hora_inicio", "")[:19] <= hasta]

    @staticmethod
    def crear_infraccion(data):
        data["id"] = _next_id["infracciones"]
        _next_id["infracciones"] += 1
        _in_memory_db["infracciones"].append(data)
        return data

    @staticmethod
    def get_infracciones_patente(patente):
        return [i for i in _in_memory_db["infracciones"] if i["patente"] == patente]

    @staticmethod
    def get_inspectores():
        return _in_memory_db["inspectores"]

    @staticmethod
    def buscar_inspector(legajo):
        return MockDB._find_one("inspectores", "legajo", legajo)

    @staticmethod
    def crear_inspector(data):
        _in_memory_db["inspectores"].append(data)
        return data

    @staticmethod
    def actualizar_inspector(legajo, data):
        for i in _in_memory_db["inspectores"]:
            if i["legajo"] == legajo:
                i.update(data)
                break

    @staticmethod
    def get_auditoria(legajo=""):
        result = _in_memory_db["auditoria"]
        if legajo:
            result = [a for a in result if a["legajo_inspector"] == legajo]
        return sorted(result, key=lambda x: x.get("creado_en", ""), reverse=True)[:100]

    @staticmethod
    def crear_auditoria(data):
        data["id"] = _next_id["auditoria"]
        _next_id["auditoria"] += 1
        data["creado_en"] = _now()
        _in_memory_db["auditoria"].append(data)

    @staticmethod
    def get_vehiculo_saldo(patente):
        return _in_memory_db["vehiculos_saldos"].get(patente, 0)

    @staticmethod
    def set_vehiculo_saldo(patente, minutos):
        _in_memory_db["vehiculos_saldos"][patente] = minutos

    @staticmethod
    def sumar_saldo_adeudado(legajo, monto):
        for i in _in_memory_db["inspectores"]:
            if i["legajo"] == legajo:
                i["saldo_adeudado"] = round(i.get("saldo_adeudado", 0) + monto, 2)
                break

    @staticmethod
    def get_ciudadano_by_chat(chat_id):
        for c in _in_memory_db["ciudadanos"]:
            if c.get("telegram_chat_id") == chat_id:
                return c
        return None

    @staticmethod
    def get_ciudadano_by_patente(patente):
        return [c for c in _in_memory_db["ciudadanos"] if patente in c.get("patentes_registradas", [])]


mock_db = MockDB()
