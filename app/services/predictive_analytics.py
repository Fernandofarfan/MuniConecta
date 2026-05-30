from collections import defaultdict

from app.database import EstacionamientoDB


async def predecir_demanda() -> list[dict]:
    from datetime import datetime, timedelta

    from app.config import TZ_ARG

    ahora = datetime.now(TZ_ARG)
    hace_30_dias = ahora - timedelta(days=30)

    registros = await EstacionamientoDB.obtener_analiticas(
        hace_30_dias.strftime("%Y-%m-%dT00:00:00-03:00"),
        ahora.strftime("%Y-%m-%dT23:59:59-03:00"),
    )

    zona_hora = defaultdict(list)
    for r in registros:
        zona_id = r.get("zona_id", "sin_zona")
        try:
            hora = datetime.fromisoformat(r["hora_inicio"].replace("Z", "+00:00")).hour
        except (ValueError, KeyError):
            continue
        zona_hora[(zona_id, hora)].append(r)

    predicciones = []
    # Usar una clave de ordenamiento segura para evitar errores de tipo al mezclar None, strings y enteros
    for (zona_id, hora), items in sorted(zona_hora.items(), key=lambda x: (str(x[0][0] or "sin_zona"), x[0][1])):
        promedio = len(items) / 30
        predicciones.append({
            "zona_id": zona_id,
            "hora": hora,
            "demanda_promedio": round(promedio, 1),
            "nivel": "alto" if promedio > 10 else "medio" if promedio > 3 else "bajo",
        })

    return predicciones
