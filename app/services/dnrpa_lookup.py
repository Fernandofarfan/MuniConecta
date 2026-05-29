import logging
import random

logger = logging.getLogger(__name__)

MARCAS = ["Fiat", "Ford", "Chevrolet", "Toyota", "Volkswagen", "Renault", "Peugeot", "Citroen", "Honda", "Nissan"]
MODELOS = {"auto": ["Cronos", "Focus", "Cruze", "Corolla", "Gol", "Sandero", "208", "C3", "Civic", "Sentra"],
           "moto": ["Titan", "Wave", "YBR", "Boxer", "CG", "Twister", "FZ", "GN", "RX", "NS"]}
COLORES = ["Blanco", "Negro", "Gris", "Rojo", "Azul", "Verde", "Plateado"]


async def consultar_dnrpa(patente: str) -> dict:
    import re

    from app.models.schemas import PATENTE_NUEVA_RE

    if PATENTE_NUEVA_RE.match(patente):
        anio = 2016 + random.randint(0, 10)
        tipo = "auto" if random.random() > 0.15 else "moto"
    else:
        anio = random.randint(1995, 2015)
        tipo = "moto" if re.match(r"^\d", patente) else "auto"

    marca = random.choice(MARCAS)
    modelo = random.choice(MODELOS.get(tipo, MODELOS["auto"]))
    color = random.choice(COLORES)
    tiene_pedido_secuestro = random.random() < 0.02
    tiene_deuda_patentes = random.random() < 0.10

    logger.info(f"DNRPA lookup: {patente} -> {marca} {modelo} ({color}), secuestro={tiene_pedido_secuestro}")

    return {
        "patente": patente,
        "marca": marca,
        "modelo": modelo,
        "anio": anio,
        "color": color,
        "tipo_vehiculo_registrado": tipo,
        "tiene_pedido_secuestro": tiene_pedido_secuestro,
        "tiene_deuda_patentes": tiene_deuda_patentes,
        "fuente": "DNRPA (mock - entorno desarrollo)",
    }
