import logging
from datetime import datetime

from app.config import TZ_ARG
from app.database import EstacionamientoDB, ZonaDB

logger = logging.getLogger(__name__)


async def detectar_anomalias() -> list[dict]:
    anomalias = []
    ahora = datetime.now(TZ_ARG)

    try:
        zonas = await ZonaDB.obtener_ocupacion()
        for zona in zonas:
            capacidad = zona.get("capacidad_maxima", 1) or 1
            ocupados = zona.get("ocupados", 0)
            pct = ocupados / capacidad * 100
            if pct > 95:
                anomalias.append({
                    "tipo": "saturacion_zona",
                    "descripcion": f"Zona {zona['nombre']} al {pct:.0f}% de capacidad ({ocupados}/{capacidad})",
                    "severidad": "alta",
                    "zona_id": zona["id"],
                    "datos": {"ocupacion_pct": round(pct, 1)},
                })
            elif pct > 80:
                anomalias.append({
                    "tipo": "saturacion_zona",
                    "descripcion": f"Zona {zona['nombre']} al {pct:.0f}% de capacidad ({ocupados}/{capacidad})",
                    "severidad": "media",
                    "zona_id": zona["id"],
                    "datos": {"ocupacion_pct": round(pct, 1)},
                })

        activos = await EstacionamientoDB.obtener_todos_activos()
        for registro in activos:
            try:
                inicio = datetime.fromisoformat(registro["hora_inicio"].replace("Z", "+00:00"))
                horas = (ahora - inicio).total_seconds() / 3600
                if horas > 8:
                    anomalias.append({
                        "tipo": "sesion_prolongada",
                        "descripcion": f"Vehiculo {registro['patente']} estacionado hace {horas:.1f}h (posible abandono)",
                        "severidad": "media",
                        "datos": {"patente": registro["patente"], "horas": round(horas, 1)},
                    })
            except (ValueError, KeyError):
                pass

    except Exception as e:
        logger.error(f"Error detectando anomalias: {e}")

    return anomalias
