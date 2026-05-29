import json
import logging

from fastapi import APIRouter, Depends, Request

from app.auth import verificar_api_key
from app.config import SUPABASE_URL
from app.database import EstacionamientoDB
from app.models.schemas import PeticionCrearPago
from app.services.comprobante import generar_comprobante_pdf, guardar_comprobante
from app.services.mercadopago import crear_preferencia_pago, obtener_pago, verificar_webhook_signature
from app.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.post("/crear")
async def crear_pago(
    peticion: PeticionCrearPago,
    _: str = Depends(verificar_api_key),
):
    registro = await EstacionamientoDB.buscar_activo_por_patente_o_error(peticion.patente)
    costo_total = registro.get("monto_final", 0) or 0

    if costo_total <= 0:
        from app.services.pricing import calcular_costo
        tipo = registro.get("tipo_vehiculo")
        inicio = registro.get("hora_inicio")
        costo_digital, _, _ = calcular_costo(tipo, inicio, "digital")

    if costo_total <= 0:
        costo_total = costo_digital

    preferencia = await crear_preferencia_pago(peticion.patente, costo_total, peticion.email)

    await EstacionamientoDB.actualizar_por_id(
        registro["id"],
        {"metodo_pago": "pendiente", "monto_final": costo_total},
    )

    return {
        "mensaje": "Link de pago generado",
        "init_point": preferencia["init_point"],
        "preference_id": preferencia.get("id"),
        "monto": costo_total,
    }


@router.post("/webhook")
async def webhook_mercadopago(request: Request):
    body = await request.json()
    logger.info(f"Webhook MP recibido: {body}")

    data_id = body.get("data", {}).get("id", "")
    x_signature = request.headers.get("x-signature", "")
    x_request_id = request.headers.get("x-request-id", "")

    if not verificar_webhook_signature(x_signature, x_request_id, data_id):
        logger.warning("Firma de webhook MP invalida")
        return {"status": "ignored"}

    pago = await obtener_pago(int(data_id)) if data_id else None

    if pago and pago.get("status") == "approved":
        patente = pago.get("external_reference", "")
        if patente:
            from datetime import datetime

            from app.config import TZ_ARG

            # Generar comprobante
            registro = await EstacionamientoDB.buscar_activo_por_patente(patente)
            if registro:
                pdf_bytes = generar_comprobante_pdf(
                    patente=patente,
                    monto=float(pago.get("transaction_amount", 0)),
                    metodo_pago="digital",
                    tiempo_minutos=0,
                    estacionamiento_id=registro["id"],
                )
                await guardar_comprobante(registro["id"], pdf_bytes)

                await EstacionamientoDB.actualizar_por_id(
                    registro["id"],
                    {
                        "metodo_pago": "digital",
                        "pago_confirmado_en": datetime.now(TZ_ARG).isoformat(),
                        "estado": "finalizado",
                    },
                )
                await manager.broadcast(json.dumps({"event": "update_dashboard"}))

    return {"status": "ok"}


@router.get("/comprobante/{estacionamiento_id}")
async def descargar_comprobante(estacionamiento_id: int):
    url = f"{SUPABASE_URL}/storage/v1/object/public/comprobantes/comprobante_{estacionamiento_id}.pdf"
    return {"url": url}
