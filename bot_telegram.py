import json
import logging
import os
import re

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

_PLATE_RE = re.compile(r"^[A-Z]{2,3}\d{3}[A-Z]{0,2}$|^\d{3}[A-Z]{3}$")


def _api_headers():
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenido a SEM Express!\n\n"
        "Enviame una patente para consultar tu deuda de estacionamiento.\n"
        "Ejemplo: AB123CD\n\n"
        "Comandos:\n"
        "/start - Este mensaje\n"
        "/deuda AB123CD - Consultar deuda\n"
        "/registrar AB123CD - Vincular patente a tu cuenta\n"
        "/mis_patentes - Ver tus patentes registradas\n"
        "/desregistrar AB123CD - Desvincular patente\n"
        "/multas AB123CD - Consultar infracciones\n"
        "/dnrpa AB123CD - Consultar registro automotor\n"
        "/abono AB123CD - Comprar abono mensual\n"
        "/historial AB123CD - Ver historial\n"
        "/apelar ID motivo - Apelar infraccion"
    )


async def cmd_deuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /deuda AB123CD")
        return
    await _procesar_consulta(update, context.args[0])


async def cmd_registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /registrar AB123CD")
        return

    patente = context.args[0].upper().strip().replace(" ", "").replace("-", "")
    if not _PLATE_RE.match(patente):
        await update.message.reply_text("Patente con formato invalido. Ejemplo: AB123CD")
        return

    chat_id = update.effective_chat.id
    nombre = update.effective_user.first_name or "Ciudadano"

    import httpx
    async with httpx.AsyncClient() as cliente:
        try:
            existing_resp = await cliente.get(
                f"{API_URL}/v1/ciudadanos/buscar?patente={patente}",
                headers=_api_headers(),
            )
            if existing_resp.status_code == 200:
                data = existing_resp.json()
                if data["total"] > 0:
                    await update.message.reply_text(f"La patente {patente} ya esta registrada por otro ciudadano.")
                    return

            ciudadano = await CiudadanoDB.buscar_por_chat_id(chat_id)
            patentes = ciudadano.get("patentes_registradas", []) if ciudadano else []
            if patente not in patentes:
                patentes.append(patente)

            resp = await cliente.post(
                f"{API_URL}/v1/ciudadanos/registrar",
                json={"telegram_chat_id": chat_id, "nombre": nombre, "patentes": patentes},
                headers=_api_headers(),
            )
            if resp.status_code == 200:
                await update.message.reply_text(
                    f"Patente {patente} registrada!\n"
                    f"Recibiras notificaciones cuando se inicie un estacionamiento."
                )
            else:
                await update.message.reply_text("Error al registrar la patente.")
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("Error de conexion con el servidor.")


async def cmd_mis_patentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    import httpx
    async with httpx.AsyncClient() as cliente:
        try:
            resp = await cliente.get(
                f"{API_URL}/v1/ciudadanos/buscar?patente=ANY",
                headers=_api_headers(),
            )
            if resp.status_code == 200:
                ciudadanos = resp.json().get("ciudadanos", [])
                propio = next((c for c in ciudadanos if c["telegram_chat_id"] == chat_id), None)
                if propio and propio.get("patentes_registradas"):
                    patentes = propio["patentes_registradas"]
                    await update.message.reply_text(f"Tus patentes: {', '.join(patentes)}")
                else:
                    await update.message.reply_text("No tenes patentes registradas. Usa /registrar AB123CD")
            else:
                await update.message.reply_text("Error al consultar patentes.")
        except Exception as e:
            await update.message.reply_text("Error de conexion.")


async def cmd_desregistrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /desregistrar AB123CD")
        return

    patente = context.args[0].upper().strip().replace(" ", "").replace("-", "")
    chat_id = update.effective_chat.id
    nombre = update.effective_user.first_name or "Ciudadano"

    import httpx
    async with httpx.AsyncClient() as cliente:
        try:
            resp = await cliente.get(
                f"{API_URL}/v1/ciudadanos/buscar?patente={patente}",
                headers=_api_headers(),
            )
            if resp.status_code == 200:
                ciudadanos = resp.json().get("ciudadanos", [])
                propio = next((c for c in ciudadanos if c["telegram_chat_id"] == chat_id), None)
                if propio and propio.get("patentes_registradas"):
                    patentes = [p for p in propio["patentes_registradas"] if p != patente]
                    register_resp = await cliente.post(
                        f"{API_URL}/v1/ciudadanos/registrar",
                        json={"telegram_chat_id": chat_id, "nombre": nombre, "patentes": patentes},
                        headers=_api_headers(),
                    )
                    if register_resp.status_code == 200:
                        await update.message.reply_text(f"Patente {patente} desregistrada.")
                    else:
                        await update.message.reply_text("Error al desregistrar.")
                else:
                    await update.message.reply_text(f"No tenes registrada la patente {patente}")
        except Exception as e:
            await update.message.reply_text("Error de conexion.")


async def cmd_multas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /multas AB123CD")
        return
    patente = context.args[0].upper().strip()
    import httpx
    async with httpx.AsyncClient() as cliente:
        try:
            resp = await cliente.get(f"{API_URL}/v1/infracciones/multas/{patente}", headers=_api_headers())
            if resp.status_code == 200:
                data = resp.json()
                multas = data.get("multas", [])
                total = data.get("total_pendiente", 0)
                if not multas:
                    await update.message.reply_text(f"La patente {patente} no tiene infracciones. Buen trabajo!")
                else:
                    texto = f"Infracciones para {patente}:\n\n"
                    for m in multas[:5]:
                        texto += f"- {m['tipo_infraccion']}: ${m['monto_multa']} ({m['estado']})\n"
                    texto += f"\nTotal pendiente: ${total}"
                    await update.message.reply_text(texto)
            else:
                await update.message.reply_text("Error al consultar infracciones.")
        except Exception:
            await update.message.reply_text("Error de conexion.")


async def cmd_dnrpa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /dnrpa AB123CD")
        return
    patente = context.args[0].upper().strip()
    import httpx
    async with httpx.AsyncClient() as cliente:
        try:
            resp = await cliente.get(f"{API_URL}/v1/dnrpa/{patente}", headers=_api_headers())
            if resp.status_code == 200:
                data = resp.json()
                texto = (
                    f"DNRPA - Consulta de {patente}:\n"
                    f"Vehiculo: {data.get('marca')} {data.get('modelo')} ({data.get('anio')})\n"
                    f"Color: {data.get('color')}\n"
                    f"Pedido de secuestro: {'SI' if data.get('tiene_pedido_secuestro') else 'No'}\n"
                    f"Deuda patentes: {'SI' if data.get('tiene_deuda_patentes') else 'No'}"
                )
                await update.message.reply_text(texto)
            elif resp.status_code == 404:
                await update.message.reply_text(f"No se encontraron datos para {patente}")
            else:
                await update.message.reply_text("Error al consultar DNRPA.")
        except Exception:
            await update.message.reply_text("Error de conexion.")


async def cmd_historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /historial AB123CD")
        return
    patente = context.args[0].upper().strip()
    import httpx
    async with httpx.AsyncClient() as cliente:
        try:
            resp = await cliente.get(f"{API_URL}/v1/vehiculos/{patente}/historial", headers=_api_headers())
            if resp.status_code == 200:
                data = resp.json()
                t = data.get("totales", {})
                e = data.get("estadisticas", {})
                a = data.get("abono_activo")
                texto = (
                    f"Historial de {patente}:\n"
                    f"Total gastado: ${t.get('total_gastado', 0)}\n"
                    f"Multas pendientes: ${t.get('total_pendiente_multas', 0)}\n"
                    f"Estacionamientos: {t.get('total_estacionamientos', 0)}\n"
                    f"Zona favorita: {e.get('zona_favorita', 'N/A')}\n"
                    f"Duracion promedio: {e.get('duracion_promedio_min', 0)}min"
                )
                if a:
                    texto += f"\n\nAbono activo hasta {a.get('fecha_fin', 'N/A')}"
                await update.message.reply_text(texto)
            else:
                await update.message.reply_text("Error al consultar historial.")
        except Exception:
            await update.message.reply_text("Error de conexion.")


async def cmd_abono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /abono AB123CD")
        return
    patente = context.args[0].upper().strip()
    import httpx
    async with httpx.AsyncClient() as cliente:
        try:
            resp = await cliente.post(
                f"{API_URL}/v1/abonos/crear",
                json={"patente": patente, "zona_id": 1, "tipo": "mensual", "chat_id": update.effective_chat.id},
                headers=_api_headers(),
            )
            if resp.status_code == 200:
                data = resp.json()
                a = data.get("abono", {})
                await update.message.reply_text(
                    f"Abono mensual creado para {patente}!\n"
                    f"Valido hasta: {a.get('fecha_fin', 'N/A')}\n"
                    f"Monto: ${a.get('monto', 0)}"
                )
            else:
                await update.message.reply_text("Error al crear abono.")
        except Exception:
            await update.message.reply_text("Error de conexion.")


async def cmd_apelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /apelar ID_INFRACCION motivo")
        return
    infraccion_id = context.args[0]
    motivo = " ".join(context.args[1:])
    import httpx
    async with httpx.AsyncClient() as cliente:
        try:
            resp = await cliente.post(
                f"{API_URL}/v1/infracciones/{infraccion_id}/apelar",
                json={"motivo": motivo},
                headers=_api_headers(),
            )
            if resp.status_code == 200:
                await update.message.reply_text("Apelacion registrada. Un supervisor la revisara.")
            else:
                await update.message.reply_text("Error al registrar apelacion.")
        except Exception:
            await update.message.reply_text("Error de conexion.")


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().upper().replace(" ", "").replace("-", "")
    if _PLATE_RE.match(texto):
        await _procesar_consulta(update, texto)
        return
    await update.message.reply_text("Envia una patente valida (ej: AB123CD) o usa /deuda AB123CD")


async def _procesar_consulta(update: Update, patente: str):
    import httpx
    async with httpx.AsyncClient() as cliente:
        try:
            respuesta = await cliente.post(
                f"{API_URL}/v1/estacionamiento/deuda",
                json={"patente": patente},
                headers=_api_headers(),
                timeout=10.0,
            )
            if respuesta.status_code == 200:
                data = respuesta.json()
                texto = (
                    f"Patente: {patente}\n"
                    f"Tiempo transcurrido: {data.get('tiempo_transcurrido_minutos')} min\n"
                    f"Monto total: ${data.get('monto_total')}\n"
                    f"Monto con MercadoPago (20% off): ${data.get('monto_con_descuento_digital')}\n"
                    f"Link de pago: {data.get('link_pago_mp')}"
                )
            elif respuesta.status_code == 404:
                texto = f"No se encontro un estacionamiento activo para {patente}"
            elif respuesta.status_code == 422:
                texto = f"Patente con formato invalido: {patente}"
            else:
                texto = f"Error del servidor ({respuesta.status_code})"
        except Exception as e:
            logger.error(f"Error consultando API: {e}")
            texto = "Error de conexion con el servidor. Intenta de nuevo mas tarde."
    await update.message.reply_text(texto)


def main():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN no configurado")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deuda", cmd_deuda))
    app.add_handler(CommandHandler("registrar", cmd_registrar))
    app.add_handler(CommandHandler("mis_patentes", cmd_mis_patentes))
    app.add_handler(CommandHandler("desregistrar", cmd_desregistrar))
    app.add_handler(CommandHandler("multas", cmd_multas))
    app.add_handler(CommandHandler("dnrpa", cmd_dnrpa))
    app.add_handler(CommandHandler("abono", cmd_abono))
    app.add_handler(CommandHandler("historial", cmd_historial))
    app.add_handler(CommandHandler("apelar", cmd_apelar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    logger.info("Bot de Telegram iniciado...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
