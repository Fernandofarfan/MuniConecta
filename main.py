import os
import math
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="SEM Express")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def obtener_headers_supabase():
    """Retorna los headers necesarios para la API de Supabase"""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

class PeticionIniciarEstacionamiento(BaseModel):
    patente: str
    tipo_vehiculo: str  # "auto" o "moto"
    legajo_permisionario: str

class PeticionCalcularCobro(BaseModel):
    patente: str
    metodo_pago: str  # "digital" o "efectivo"

@app.post("/iniciar_estacionamiento")
async def iniciar_estacionamiento(peticion: PeticionIniciarEstacionamiento):
    if peticion.tipo_vehiculo not in ["auto", "moto"]:
        raise HTTPException(status_code=400, detail="El tipo de vehículo debe ser 'auto' o 'moto'")
        
    url = f"{SUPABASE_URL}/rest/v1/estacionamientos"
    ahora = datetime.now(timezone.utc).isoformat()
    patente_limpia = peticion.patente.upper().strip()
    
    carga_datos = {
        "patente": patente_limpia,
        "tipo_vehiculo": peticion.tipo_vehiculo,
        "legajo_permisionario": peticion.legajo_permisionario,
        "hora_inicio": ahora,
        "estado": "activo"
    }
    
    async with httpx.AsyncClient() as cliente:
        # Verificar si la patente ya tiene un estacionamiento activo
        url_verificacion = f"{url}?patente=eq.{patente_limpia}&estado=eq.activo"
        respuesta_verificacion = await cliente.get(url_verificacion, headers=obtener_headers_supabase())
        
        if respuesta_verificacion.status_code == 200 and len(respuesta_verificacion.json()) > 0:
            raise HTTPException(status_code=400, detail="El vehículo ya tiene un estacionamiento activo en curso")
            
        # Iniciar estacionamiento
        respuesta = await cliente.post(url, headers=obtener_headers_supabase(), json=carga_datos)
        if respuesta.status_code not in [201, 204]:
            raise HTTPException(status_code=500, detail="Error al guardar el registro en Supabase")
            
    return {"mensaje": "Estacionamiento iniciado correctamente", "datos": carga_datos}

@app.post("/calcular_cobro")
async def calcular_cobro(peticion: PeticionCalcularCobro):
    if peticion.metodo_pago not in ["digital", "efectivo"]:
        raise HTTPException(status_code=400, detail="El método de pago debe ser 'digital' o 'efectivo'")
        
    url = f"{SUPABASE_URL}/rest/v1/estacionamientos"
    patente_limpia = peticion.patente.upper().strip()
    
    async with httpx.AsyncClient() as cliente:
        # Buscar el estacionamiento activo para esta patente
        url_busqueda = f"{url}?patente=eq.{patente_limpia}&estado=eq.activo&select=*"
        respuesta_busqueda = await cliente.get(url_busqueda, headers=obtener_headers_supabase())
        
        if respuesta_busqueda.status_code != 200 or len(respuesta_busqueda.json()) == 0:
            raise HTTPException(status_code=404, detail="No se encontró un estacionamiento activo para esta patente")
            
        registro = respuesta_busqueda.json()[0]
        tipo_vehiculo = registro.get("tipo_vehiculo")
        hora_inicio_str = registro.get("hora_inicio")
        
        # Procesar fechas y tiempos
        hora_inicio = datetime.fromisoformat(hora_inicio_str.replace("Z", "+00:00"))
        hora_fin = datetime.now(timezone.utc)
        
        delta_tiempo = hora_fin - hora_inicio
        minutos_transcurridos = delta_tiempo.total_seconds() / 60
        
        # Lógica de negocio estricta
        tarifa_base = 700 if tipo_vehiculo == "auto" else 300
        costo_total = 0
        
        if minutos_transcurridos < 5:
            # Tolerancia de 5 minutos
            costo_total = 0
        elif minutos_transcurridos <= 60:
            # Primera hora se cobra completa
            costo_total = tarifa_base
        else:
            # A partir de la segunda hora, se cobra fraccionado cada 15 minutos exactos
            minutos_adicionales = minutos_transcurridos - 60
            fracciones_15_minutos = math.ceil(minutos_adicionales / 15)
            costo_total = tarifa_base + (fracciones_15_minutos * (tarifa_base / 4))
            
        # Incentivo digital: 20% de descuento
        if peticion.metodo_pago == "digital" and costo_total > 0:
            costo_total = costo_total * 0.8
            
        # Actualizar el registro en Supabase asegurando la trazabilidad
        ahora_iso = hora_fin.isoformat()
        carga_actualizacion = {
            "estado": "finalizado",
            "hora_fin": ahora_iso,
            "monto_final": costo_total,
            "metodo_pago": peticion.metodo_pago
        }
        
        # Usamos update/patch buscando por patente y estado activo
        url_actualizacion = f"{url}?patente=eq.{patente_limpia}&estado=eq.activo"
        headers_patch = obtener_headers_supabase()
        headers_patch["Prefer"] = "return=representation"
        
        respuesta_actualizacion = await cliente.patch(url_actualizacion, headers=headers_patch, json=carga_actualizacion)
        
        if respuesta_actualizacion.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail="Error al actualizar el registro del cobro en Supabase")
            
    return {
        "mensaje": "Estacionamiento finalizado y cobro calculado",
        "patente": patente_limpia,
        "tiempo_transcurrido_minutos": round(minutos_transcurridos, 2),
        "monto_final": costo_total,
        "metodo_pago": peticion.metodo_pago
    }
