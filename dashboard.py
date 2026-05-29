import os

from dotenv import load_dotenv

load_dotenv()

from datetime import UTC, datetime, timedelta

import google.generativeai as genai
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=10000, key="data_refresh")

st.set_page_config(page_title="SEM Express", page_icon="🚗", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.1);
        padding: 20px 25px; border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.2);
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(0,177,234,0.3);
        border: 1px solid rgba(0,177,234,0.4);
    }
    h1 {
        background: linear-gradient(45deg, #00b1ea, #85bb65, #00b1ea);
        background-size: 200% 200%;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 800 !important; text-align: center;
        animation: gradient_anim 5s ease infinite;
    }
    @keyframes gradient_anim {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .stMarkdown p { text-align: center; font-size: 1.2rem; color: #a0aabf; }
    .stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.15); }
</style>
""", unsafe_allow_html=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def obtener_headers_supabase():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _api_headers():
    h = {}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def cargar_datos_estacionamientos():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Credenciales de Supabase no configuradas.")
        return []
    url = f"{SUPABASE_URL}/rest/v1/estacionamientos?select=*"
    respuesta = requests.get(url, headers=obtener_headers_supabase())
    if respuesta.status_code == 200:
        return respuesta.json()
    elif respuesta.status_code == 404:
        st.error("Tabla 'estacionamientos' no encontrada.")
        st.info("Ejecuta las migraciones en supabase/migrations/")
        return None
    else:
        st.error(f"Error: {respuesta.status_code}")
        return None


def cargar_zonas():
    try:
        res = requests.get(f"{API_URL}/v1/zonas/ocupacion", headers=_api_headers())
        if res.status_code == 200:
            return res.json().get("zonas", [])
    except Exception:
        pass
    return []


def cargar_analiticas(dias=30):
    desde = (datetime.now(UTC) - timedelta(days=dias)).strftime("%Y-%m-%d")
    hasta = datetime.now(UTC).strftime("%Y-%m-%d")
    try:
        res = requests.get(
            f"{API_URL}/v1/analiticas/estadisticas?desde={desde}&hasta={hasta}&agrupacion=dia",
            headers=_api_headers(),
        )
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


def cargar_datos_zonas():
    try:
        res = requests.get(f"{API_URL}/v1/zonas", headers=_api_headers())
        if res.status_code == 200:
            return res.json().get("zonas", [])
    except Exception:
        pass
    return []


with st.sidebar:
    st.header("📱 App Permisionario")
    st.link_button("💬 Abrir Bot en Telegram", "https://t.me/MuniConecta_Bot", use_container_width=True)

    st.subheader("📸 Escáner OCR Inteligente")
    if st.button("📷 Simular Lectura de Patente"):
        with st.spinner("Analizando imagen..."):
            try:
                res = requests.post(
                    f"{API_URL}/v1/escanear_patente",
                    json={"imagen_base64": "mock_data"},
                    headers=_api_headers(),
                )
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"✅ Patente: {data['patente_detectada']} (Confianza: {data['confianza']*100}%)")
                else:
                    st.error("Error en el reconocimiento")
            except Exception:
                st.error("Fallo de conexión OCR.")

    st.divider()

    st.subheader("1. Entrada de Vehículo")
    with st.form("form_iniciar"):
        patente = st.text_input("Patente (Ej: AB123CD)").upper()
        tipo = st.selectbox("Tipo", ["auto", "moto"])
        legajo = st.text_input("Tu Legajo", value="INSP-01")
        submit_iniciar = st.form_submit_button("✅ Iniciar Estacionamiento")
        if submit_iniciar and patente:
            with st.spinner("Registrando..."):
                try:
                    res = requests.post(
                        f"{API_URL}/v1/estacionamiento/iniciar",
                        json={"patente": patente, "tipo_vehiculo": tipo, "legajo_permisionario": legajo},
                        headers=_api_headers(),
                    )
                    if res.status_code == 200:
                        st.success("¡Vehículo registrado!")
                    else:
                        st.error(res.json().get("detail", "Error"))
                except Exception:
                    st.error("Fallo de conexión.")
        elif submit_iniciar:
            st.warning("Escribe una patente.")

    st.divider()

    st.subheader("2. Salida y Cobro")
    with st.form("form_cobrar"):
        patente_cobro = st.text_input("Patente a retirar").upper()
        metodo = st.selectbox("Método de Pago", ["digital", "efectivo"])
        submit_cobrar = st.form_submit_button("💸 Calcular y Cobrar")
        if submit_cobrar and patente_cobro:
            with st.spinner("Calculando..."):
                try:
                    res = requests.post(
                        f"{API_URL}/v1/estacionamiento/cobrar",
                        json={"patente": patente_cobro, "metodo_pago": metodo},
                        headers=_api_headers(),
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"Total a cobrar: ${data['monto_final']}")
                        if data.get("link_pago_mp"):
                            st.markdown(f"[💳 Abrir Link de Pago]({data['link_pago_mp']})")
                    else:
                        st.error(res.json().get("detail", "Auto no encontrado"))
                except Exception:
                    st.error("Fallo de conexión.")
        elif submit_cobrar:
            st.warning("Escribe la patente.")

st.title("SEM Express")
st.markdown("Panel de Control Inteligente de Estacionamiento Medido")

datos = cargar_datos_estacionamientos()

if datos is None:
    st.stop()
elif not datos:
    st.info("No hay datos de estacionamientos registrados en el sistema.")
else:
    df = pd.DataFrame(datos)
    columnas_esperadas = [
        "estado", "monto_final", "metodo_pago", "hora_inicio", "hora_fin",
        "patente", "legajo_permisionario", "lat", "lon", "zona_id",
    ]
    for col in columnas_esperadas:
        if col not in df.columns:
            df[col] = None

    df["monto_final"] = pd.to_numeric(df["monto_final"], errors="coerce").fillna(0)
    df["hora_inicio_dt"] = pd.to_datetime(df["hora_inicio"], errors="coerce")
    df["fecha_inicio"] = df["hora_inicio_dt"].dt.date
    df["hora_fin_dt"] = pd.to_datetime(df["hora_fin"], errors="coerce")
    df["fecha_fin"] = df["hora_fin_dt"].dt.date
    df["fecha_fin"] = df["fecha_fin"].fillna(df["fecha_inicio"])

    hoy = datetime.now(UTC).date()
    df_activos = df[df["estado"] == "activo"]
    vehiculos_activos = len(df_activos)

    df_finalizados_hoy = df[(df["estado"] == "finalizado") & (df["fecha_fin"] == hoy)]
    recaudacion_cerrada = df_finalizados_hoy["monto_final"].sum()
    deuda_activa = df_activos["monto_final"].sum()
    recaudacion_hoy = recaudacion_cerrada + deuda_activa

    df_pagos_validos = df[(df["estado"] == "finalizado") & (df["metodo_pago"].notna()) & (df["metodo_pago"] != "")]
    total_pagos = len(df_pagos_validos)
    pagos_digitales = len(df_pagos_validos[df_pagos_validos["metodo_pago"] == "digital"])
    porcentaje_digital = (pagos_digitales / total_pagos * 100) if total_pagos > 0 else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("🚗 Estacionados Ahora", vehiculos_activos)
    col2.metric("💰 Recaudación del Día", f"${recaudacion_hoy:,.2f}")
    col3.metric("📱 Adopción Pago Digital", f"{porcentaje_digital:.1f}%")

    st.divider()

    st.subheader("🗺️ Mapa de Ocupación en Tiempo Real")
    if not df_activos.empty:
        df_map = df_activos.copy()
        if df_map["lat"].notna().any() and df_map["lon"].notna().any():
            st.map(df_map[["lat", "lon"]].dropna(), zoom=14)
        else:
            df_map["lat"] = -24.7883 + np.random.normal(0, 0.002, size=len(df_map))
            df_map["lon"] = -65.4105 + np.random.normal(0, 0.002, size=len(df_map))
            st.map(df_map[["lat", "lon"]], zoom=14)
    else:
        st.info("No hay vehículos estacionados para mostrar en el mapa.")

    st.divider()

    zonas_data = cargar_zonas()
    if zonas_data:
        st.subheader("📊 Ocupación por Zona")
        cols_zona = st.columns(len(zonas_data))
        for i, zona in enumerate(zonas_data):
            with cols_zona[i]:
                pct = (zona["ocupados"] / zona["capacidad_maxima"] * 100) if zona["capacidad_maxima"] > 0 else 0
                st.metric(
                    f"📍 {zona['nombre']}",
                    f"{zona['ocupados']}/{zona['capacidad_maxima']}",
                    f"{pct:.0f}% ocupado",
                )

    st.divider()

    st.subheader("📈 Tendencias (30 días)")
    analiticas = cargar_analiticas(30)
    if analiticas and analiticas.get("serie_temporal"):
        serie = analiticas["serie_temporal"]
        df_serie = pd.DataFrame(serie)
        if not df_serie.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_serie["periodo"], y=df_serie["recaudacion"],
                mode="lines+markers", name="Recaudación",
                line={"color": "#00b1ea"}, fill="tozeroy",
                fillcolor="rgba(0,177,234,0.1)",
            ))
            fig.update_layout(
                margin={"t": 20, "b": 20, "l": 20, "r": 20},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
                xaxis={"title": None},
                yaxis={"title": "Recaudación ($)", "gridcolor": "rgba(255,255,255,0.1)"},
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Total Estacionamientos", analiticas["total_estacionamientos"])
            col_b.metric("Recaudación Total", f"${analiticas['recaudacion_total']:,.2f}")
            col_c.metric("Duración Promedio", f"{analiticas['duracion_promedio_minutos']:.0f} min")

    st.divider()

    st.subheader("🤖 Intendente AI - Análisis Ejecutivo")
    if st.button("Generar Reporte Estratégico con IA"):
        if not GEMINI_API_KEY:
            st.error("⚠️ Falta configurar GEMINI_API_KEY en el archivo .env")
        else:
            with st.spinner("Analizando métricas..."):
                try:
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    prompt = (
                        f"Actua como analista de datos del SEM de la Municipalidad de Salta. "
                        f"Hay {vehiculos_activos} autos estacionados, recaudacion ${recaudacion_hoy:,.2f}, "
                        f"{porcentaje_digital:.1f}% pago digital. "
                        f"Redacta un reporte ejecutivo corto (1 parrafo) para el Intendente, "
                        f"sugiriendo una accion operativa en la calle basandote en estos datos."
                    )
                    respuesta = model.generate_content(prompt)
                    st.info(respuesta.text)
                except Exception as e:
                    st.error(f"Error al generar el reporte: {e}")

    st.divider()

    st.subheader("⚙️ Administración del Sistema")
    col_admin1, col_admin2 = st.columns(2)
    with col_admin1:
        if st.button("⚠️ Ejecutar Cierre Diario Forzado", use_container_width=True):
            with st.spinner("Cerrando sesiones activas..."):
                try:
                    res = requests.post(f"{API_URL}/v1/cierre_diario_forzado", headers=_api_headers())
                    if res.status_code == 200:
                        st.success("Cierre ejecutado")
                        st.rerun()
                    else:
                        st.error("Error al ejecutar cierre")
                except Exception:
                    st.error("Error de conexión.")

    st.divider()

    col_grafico, col_tabla = st.columns(2, gap="large")
    with col_grafico:
        st.subheader("📊 Métodos de Pago")
        if total_pagos > 0:
            conteo_pagos = df_pagos_validos["metodo_pago"].value_counts().reset_index()
            conteo_pagos.columns = ["Método de Pago", "Cantidad"]
            conteo_pagos["Método de Pago"] = conteo_pagos["Método de Pago"].replace(
                {"digital": "Mercado Pago", "efectivo": "Efectivo"}
            )
            fig = px.pie(
                conteo_pagos, values="Cantidad", names="Método de Pago",
                hole=0.5, color_discrete_sequence=["#00b1ea", "#85bb65"],
            )
            fig.update_layout(
                margin={"t": 20, "b": 20, "l": 20, "r": 20},
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos suficientes.")

    with col_tabla:
        st.subheader("📡 Radar en Tiempo Real")
        if not df_activos.empty:
            tabla_mostrar = df_activos[["patente", "hora_inicio", "legajo_permisionario"]].copy()
            tabla_mostrar["hora_inicio"] = pd.to_datetime(tabla_mostrar["hora_inicio"]).dt.strftime("%H:%M:%S")
            tabla_mostrar.columns = ["Patente", "Hora Entrada", "Permisionario"]
            st.dataframe(tabla_mostrar, use_container_width=True, hide_index=True, height=400)
        else:
            st.info("Plazas de estacionamiento liberadas.")
