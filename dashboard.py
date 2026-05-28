import os
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
import plotly.express as px

# Configuración inicial de la página
st.set_page_config(page_title="SEM Express", page_icon="🚗", layout="wide")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def obtener_headers_supabase():
    """Retorna los headers para conectarse a Supabase de forma segura"""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

def cargar_datos_estacionamientos():
    """Obtiene todos los registros de estacionamiento desde Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Credenciales de Supabase no configuradas. Revisa las variables de entorno.")
        return []
        
    url = f"{SUPABASE_URL}/rest/v1/estacionamientos?select=*"
    respuesta = requests.get(url, headers=obtener_headers_supabase())
    if respuesta.status_code == 200:
        return respuesta.json()
    else:
        st.error(f"Error al conectar con Supabase: {respuesta.status_code}")
        return []

st.title("🚗 SEM Express - Panel de Control")
st.markdown("Sistema de Estacionamiento Medido Municipal")

datos = cargar_datos_estacionamientos()

if not datos:
    st.info("No hay datos de estacionamientos registrados en el sistema.")
else:
    df = pd.DataFrame(datos)
    
    # Validar que existan las columnas necesarias, para evitar errores si la base está vacía o es nueva
    columnas_esperadas = ["estado", "monto_final", "metodo_pago", "hora_inicio", "hora_fin", "patente", "legajo_permisionario"]
    for col in columnas_esperadas:
        if col not in df.columns:
            df[col] = None
            
    # Convertir montos a numérico para poder operar
    df['monto_final'] = pd.to_numeric(df['monto_final'], errors='coerce').fillna(0)
    
    # Procesar fechas
    df['hora_inicio_dt'] = pd.to_datetime(df['hora_inicio'], errors='coerce')
    df['fecha_inicio'] = df['hora_inicio_dt'].dt.date
    df['hora_fin_dt'] = pd.to_datetime(df['hora_fin'], errors='coerce')
    df['fecha_fin'] = df['hora_fin_dt'].dt.date
    # Si no tiene fecha de fin, usamos la de inicio para tener una referencia
    df['fecha_fin'] = df['fecha_fin'].fillna(df['fecha_inicio'])
    
    # --- MÉTRICAS CLAVE ---
    hoy = datetime.now(timezone.utc).date()
    
    # 1. Vehículos Estacionados Ahora
    df_activos = df[df['estado'] == 'activo']
    vehiculos_activos = len(df_activos)
    
    # 2. Recaudación del Día (suma de montos finalizados de hoy)
    df_finalizados_hoy = df[(df['estado'] == 'finalizado') & (df['fecha_fin'] == hoy)]
    recaudacion_hoy = df_finalizados_hoy['monto_final'].sum()
    
    # 3. Adopción de Pago Digital
    # Analizamos todos los pagos finalizados para sacar la estadística
    df_pagos_validos = df[(df['estado'] == 'finalizado') & (df['metodo_pago'].notna()) & (df['metodo_pago'] != "")]
    total_pagos = len(df_pagos_validos)
    pagos_digitales = len(df_pagos_validos[df_pagos_validos['metodo_pago'] == 'digital'])
    
    porcentaje_digital = 0.0
    if total_pagos > 0:
        porcentaje_digital = (pagos_digitales / total_pagos) * 100
        
    # Mostrar las métricas en 3 columnas
    col1, col2, col3 = st.columns(3)
    col1.metric("Vehículos Estacionados Ahora", vehiculos_activos)
    col2.metric("Recaudación del Día", f"${recaudacion_hoy:,.2f}")
    col3.metric("Adopción de Pago Digital", f"{porcentaje_digital:.1f}%")
    
    st.divider()
    
    # --- GRÁFICOS Y TABLAS ---
    col_grafico, col_tabla = st.columns(2)
    
    with col_grafico:
        st.subheader("Proporción de Métodos de Pago")
        if total_pagos > 0:
            # Preparar datos para el gráfico circular
            conteo_pagos = df_pagos_validos['metodo_pago'].value_counts().reset_index()
            conteo_pagos.columns = ['Método de Pago', 'Cantidad']
            
            # Renombrar para que quede mejor visualmente
            conteo_pagos['Método de Pago'] = conteo_pagos['Método de Pago'].replace({
                'digital': 'Mercado Pago (Digital)', 
                'efectivo': 'Efectivo'
            })
            
            fig = px.pie(
                conteo_pagos, 
                values='Cantidad', 
                names='Método de Pago', 
                hole=0.4, 
                color_discrete_sequence=['#00b1ea', '#85bb65'] # Azul Mercado Pago y Verde Efectivo
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aún no hay suficientes datos de transacciones finalizadas para mostrar estadísticas de pagos.")
            
    with col_tabla:
        st.subheader("Registro en Tiempo Real")
        if not df_activos.empty:
            # Mostrar tabla con la información en vivo
            tabla_mostrar = df_activos[['patente', 'hora_inicio', 'legajo_permisionario']].copy()
            
            # Formatear la hora de inicio para mejor lectura
            tabla_mostrar['hora_inicio'] = pd.to_datetime(tabla_mostrar['hora_inicio']).dt.strftime('%H:%M:%S (%d/%m)')
            
            # Renombrar columnas al español
            tabla_mostrar.columns = ['Patente', 'Hora de Entrada', 'Legajo Permisionario']
            
            st.dataframe(tabla_mostrar, use_container_width=True, hide_index=True)
        else:
            st.info("Actualmente no hay vehículos registrados ocupando lugares de estacionamiento.")
