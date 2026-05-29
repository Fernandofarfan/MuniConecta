from __future__ import annotations

import logging
import math
from datetime import datetime

from app.config import DESCUENTO_DIGITAL, TOLERANCIA_MINUTOS, TZ_ARG, get_tarifa

logger = logging.getLogger(__name__)


def calcular_costo(
    tipo_vehiculo: str,
    hora_inicio_str: str,
    metodo_pago: str = "efectivo",
    hora_fin: datetime | None = None,
) -> tuple[float, float, datetime]:
    try:
        hora_inicio = datetime.fromisoformat(hora_inicio_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        hora_inicio = datetime.now(TZ_ARG)

    if hora_fin is None:
        hora_fin = datetime.now(TZ_ARG)
    delta = hora_fin - hora_inicio
    minutos_transcurridos = delta.total_seconds() / 60.0

    tarifa_base = get_tarifa(tipo_vehiculo)

    if minutos_transcurridos < TOLERANCIA_MINUTOS:
        costo_total = 0.0
    elif minutos_transcurridos <= 60:
        costo_total = float(tarifa_base)
    else:
        minutos_adicionales = minutos_transcurridos - 60
        fracciones = math.ceil(minutos_adicionales / 15)
        costo_total = tarifa_base + (fracciones * (tarifa_base / 4))

    if metodo_pago == "digital" and costo_total > 0:
        costo_total = costo_total * DESCUENTO_DIGITAL

    return round(costo_total, 2), round(minutos_transcurridos, 2), hora_fin
