import logging
import math

logger = logging.getLogger(__name__)

GEOFENCE_RADIUS_METERS = 500


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def detectar_zona_por_gps(lat: float, lon: float) -> dict | None:
    from app.database import ZonaDB

    zonas = await ZonaDB.obtener_todas()
    if not zonas:
        return None

    mejor_zona = None
    mejor_distancia = float("inf")

    for zona in zonas:
        z_lat = zona.get("centro_lat")
        z_lon = zona.get("centro_lon")
        if z_lat is None or z_lon is None:
            continue
        distancia = haversine_meters(lat, lon, z_lat, z_lon)
        if distancia < mejor_distancia and distancia <= GEOFENCE_RADIUS_METERS:
            mejor_distancia = distancia
            mejor_zona = zona

    if mejor_zona:
        logger.info(f"Geofence: ({lat},{lon}) -> {mejor_zona['nombre']} ({mejor_distancia:.0f}m)")
        return {"zona_id": mejor_zona["id"], "zona_nombre": mejor_zona["nombre"], "distancia_m": round(mejor_distancia)}

    logger.info(f"Geofence: ({lat},{lon}) fuera de rango de todas las zonas")
    return None
