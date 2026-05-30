import os
import pathlib
from dotenv import load_dotenv

# Cargar .env con ruta absoluta relativa al archivo para garantizar que se encuentre
_ENV_PATH = pathlib.Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=True)

from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# set_page_config DEBE ser el primer comando de Streamlit
st.set_page_config(page_title="SEM Express", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")

# Refrescar cada 60 segundos
st_autorefresh(interval=60000, key="data_refresh")

# Importar Gemini SDK (nuevo google-genai o fallback a google-generativeai)
try:
    from google import genai as _genai_new
    _GENAI_SDK = "new"
except ImportError:
    try:
        import google.generativeai as _genai_legacy
        _GENAI_SDK = "legacy"
    except ImportError:
        _GENAI_SDK = None

# ── CSS Premium ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.1); padding: 20px 25px; border-radius: 15px;
    box-shadow: 0 8px 32px 0 rgba(0,0,0,0.2); backdrop-filter: blur(10px);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-5px); box-shadow: 0 12px 40px 0 rgba(0,177,234,0.3);
    border: 1px solid rgba(0,177,234,0.4);
}
h1 {
    background: linear-gradient(45deg, #00b1ea, #85bb65, #00b1ea); background-size: 200% 200%;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    font-weight: 800 !important; text-align: center; animation: gradient_anim 5s ease infinite;
}
@keyframes gradient_anim { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    padding: 10px 20px; border-radius: 8px; background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1); color: #a0aabf;
}
.stTabs [aria-selected="true"] { background: rgba(0,177,234,0.15); color: #00b1ea; border-color: #00b1ea; }
.stButton > button {
    background: linear-gradient(135deg, #00b1ea, #0091c7); color: white; border: none;
    border-radius: 10px; padding: 10px 20px; font-weight: 600; width: 100%;
}
.stButton > button:hover { opacity: 0.9; }
.alert-card {
    padding: 12px 18px; border-radius: 10px; margin: 5px 0; font-size: 0.9rem;
    border-left: 4px solid;
}
.alert-alta { background: rgba(239,68,68,0.1); border-color: #ef4444; color: #fca5a5; }
.alert-media { background: rgba(234,179,8,0.1); border-color: #eab308; color: #fde047; }
.alert-baja { background: rgba(34,197,94,0.1); border-color: #22c55e; color: #86efac; }
</style>
""", unsafe_allow_html=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def obtener_headers_supabase():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


def _api_headers():
    h = {}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def _api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", headers=_api_headers(), params=params, timeout=10)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def _api_post(path, json_data):
    try:
        url = f"{API_URL}{path}"
        r = requests.post(url, json=json_data, headers=_api_headers(), timeout=10)
        if r.status_code in (200, 201):
            return r.json()
        try:
            detail = r.json().get("detail", r.text[:200])
        except Exception:
            detail = r.text[:200]
        return {"error": detail, "status": r.status_code, "url": url}
    except requests.exceptions.ConnectionError:
        return {"error": f"No se pudo conectar a la API en {API_URL}. Verifica que uvicorn este corriendo (uvicorn app.main:app --port 8000)"}
    except Exception as e:
        return {"error": str(e)}


def cargar_datos_estacionamientos():
    if not SUPABASE_URL or not SUPABASE_KEY:
        data = _api_get("/v1/estacionamientos/mock-data")
        if data:
            return data
        return []
    r = requests.get(f"{SUPABASE_URL}/rest/v1/estacionamientos?select=*&limit=500", headers=obtener_headers_supabase())
    return r.json() if r.status_code == 200 else []


def cargar_datos_infracciones():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    r = requests.get(f"{SUPABASE_URL}/rest/v1/infracciones?select=*&limit=200", headers=obtener_headers_supabase())
    return r.json() if r.status_code == 200 else []


def cargar_auditoria(legajo=""):
    params = {"limit": 100}
    if legajo:
        params["legajo"] = legajo
    return _api_get("/v1/auditoria", params)


def cargar_inspectores():
    return _api_get("/v1/admin/inspectores")


# ═══════════════ SIDEBAR ═══════════════
with st.sidebar:
    st.title("🚗 SEM Express")

    api_status = _api_get("/health")
    if api_status and api_status.get("status") == "ok":
        st.success("API conectada")
    else:
        st.error(f"API no detectada en {API_URL}")
        st.info("Ejecuta: uvicorn app.main:app --port 8000")
        st.code("API_URL=http://127.0.0.1:8000", language="env")

    st.link_button("💬 Bot Telegram", "https://t.me/MuniConecta_Bot", use_container_width=True)

    accion = st.selectbox("Accion Inspector", [
        "🚘 Iniciar Estacionamiento", "💸 Cobrar Estacionamiento",
        "🚨 Emitir Infraccion", "🔍 Consultar DNRPA",
        "📋 Crear Abono", "📸 OCR Patente",
    ])

    if accion == "🚘 Iniciar Estacionamiento":
        with st.form("form_iniciar"):
            pat = st.text_input("Patente").upper()
            tipo = st.selectbox("Tipo", ["auto", "moto"])
            legajo = st.text_input("Legajo", "INSP-01")
            lat = st.number_input("Latitud", value=-24.7883, format="%.4f")
            lon = st.number_input("Longitud", value=-65.4105, format="%.4f")
            if st.form_submit_button("✅ Iniciar") and pat:
                res = _api_post("/v1/estacionamiento/iniciar", {"patente": pat, "tipo_vehiculo": tipo, "legajo_permisionario": legajo, "lat": lat, "lon": lon})
                if "error" in res:
                    st.error(res.get("error") or res.get("detail", "Error"))
                else:
                    zona = res.get("zona_detectada", "Auto")
                    abono = " (Abono activo)" if res.get("abono_activo") else ""
                    st.success(f"Registrado! Zona: {zona}{abono}")

    elif accion == "💸 Cobrar Estacionamiento":
        with st.form("form_cobrar"):
            pat = st.text_input("Patente a retirar").upper()
            met = st.selectbox("Pago", ["efectivo", "digital"])
            if st.form_submit_button("💳 Cobrar") and pat:
                res = _api_post("/v1/estacionamiento/cobrar", {"patente": pat, "metodo_pago": met})
                if "error" in res:
                    st.error(res.get("error") or res.get("detail", "Error"))
                else:
                    st.success(f"Total: ${res['monto_final']}")
                    if res.get("link_pago_mp"):
                        st.markdown(f"[💳 Pagar]({res['link_pago_mp']})")

    elif accion == "🚨 Emitir Infraccion":
        with st.form("form_infraccion"):
            pat = st.text_input("Patente").upper()
            tipo_inf = st.selectbox("Tipo", ["sin_registro", "mal_estacionado", "exceso_tiempo"])
            obs = st.text_area("Observaciones")
            if st.form_submit_button("🚨 Emitir") and pat:
                res = _api_post("/v1/infracciones/emitir", {"patente": pat, "tipo_infraccion": tipo_inf, "observaciones": obs, "legajo_inspector": "INSP-01"})
                if "error" in res:
                    st.error(res.get("error") or res.get("detail", "Error"))
                else:
                    monto = res.get("infraccion", {}).get("monto_multa", 0)
                    st.success(f"Infraccion emitida! Monto: ${monto}")

    elif accion == "🔍 Consultar DNRPA":
        pat = st.text_input("Patente a consultar").upper()
        if st.button("🔍 Consultar") and pat:
            res = requests.get(f"{API_URL}/v1/dnrpa/{pat}", headers=_api_headers())
            if res.status_code == 200:
                d = res.json()
                st.info(f"{d.get('marca')} {d.get('modelo')} ({d.get('anio')}) - {d.get('color')}")
                if d.get("tiene_pedido_secuestro"):
                    st.error("🚨 PEDIDO DE SECUESTRO ACTIVO")
                if d.get("tiene_deuda_patentes"):
                    st.warning("Tiene deuda de patentes")

    elif accion == "📋 Crear Abono":
        with st.form("form_abono"):
            pat = st.text_input("Patente").upper()
            tipo_ab = st.selectbox("Tipo", ["mensual", "semanal"])
            if st.form_submit_button("📋 Crear Abono") and pat:
                res = _api_post("/v1/abonos/crear", {"patente": pat, "tipo": tipo_ab, "zona_id": 1})
                if "error" in res:
                    st.error(res.get("error", "Error"))
                else:
                    a = res.get("abono", {})
                    st.success(f"Abono {tipo_ab} creado hasta {a.get('fecha_fin', 'N/A')}")

    elif accion == "📸 OCR Patente":
        if st.button("📷 Escanear"):
            res = _api_post("/v1/escanear_patente", {"imagen_base64": "mock"})
            if "error" in res:
                st.error("Error OCR")
            else:
                st.success(f"Patente: {res['patente_detectada']} ({res['confianza']*100:.0f}%)")

st.title("SEM Express")
st.markdown("Panel de Control Inteligente | Municipalidad de Salta")

# ── Cargar datos base ──
datos = cargar_datos_estacionamientos()
df = None
if datos:
    df = pd.DataFrame(datos)
    for col in ["estado", "monto_final", "metodo_pago", "hora_inicio", "hora_fin", "patente", "legajo_permisionario", "lat", "lon", "zona_id"]:
        if col not in df.columns:
            df[col] = None
    df["monto_final"] = pd.to_numeric(df["monto_final"], errors="coerce").fillna(0)
    df["hora_inicio_dt"] = pd.to_datetime(df["hora_inicio"], errors="coerce")
    df["hora_fin_dt"] = pd.to_datetime(df["hora_fin"], errors="coerce")
    df["fecha_fin"] = df["hora_fin_dt"].dt.date

hoy = datetime.now(UTC).date()
df_activos = df[df["estado"] == "activo"] if df is not None and not df.empty else pd.DataFrame()
vehiculos_activos = len(df_activos)
recaudacion_hoy = 0.0
porcentaje_digital = 0.0
total_pagos = 0

if df is not None and not df.empty:
    df_fin_hoy = df[(df["estado"] == "finalizado") & (df["fecha_fin"] == hoy)]
    recaudacion_hoy = df_fin_hoy["monto_final"].sum() + df_activos["monto_final"].sum()
    df_pagos = df[(df["estado"] == "finalizado") & (df["metodo_pago"].notna()) & (df["metodo_pago"] != "")]
    total_pagos = len(df_pagos)
    if total_pagos > 0:
        porcentaje_digital = len(df_pagos[df_pagos["metodo_pago"] == "digital"]) / total_pagos * 100

# ═══════════════ TABS ═══════════════
t1, t2, t3, t4, t5 = st.tabs(["📊 Monitoreo", "🚗 Vehiculos", "🚨 Infracciones", "⚙️ Administracion", "📋 Auditoria"])

# ── TAB 1: Monitoreo ──
with t1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🚗 Estacionados", vehiculos_activos)
    c2.metric("💰 Recaudacion Hoy", f"${recaudacion_hoy:,.0f}")
    c3.metric("📱 Digital", f"{porcentaje_digital:.0f}%")
    infracciones_data = cargar_datos_infracciones()
    pendientes_multas = sum(1 for i in infracciones_data if i.get("estado") == "pendiente") if infracciones_data else 0
    c4.metric("🚨 Multas Pendientes", pendientes_multas)

    st.divider()
    col_mapa, col_alertas = st.columns([2, 1])

    with col_mapa:
        st.subheader("🗺️ Mapa de Ocupacion")
        if not df_activos.empty:
            df_map = df_activos.copy()
            if df_map["lat"].notna().any():
                st.map(df_map[["lat", "lon"]].dropna(), zoom=14)
            else:
                df_map["lat"] = -24.7883 + np.random.normal(0, 0.002, size=len(df_map))
                df_map["lon"] = -65.4105 + np.random.normal(0, 0.002, size=len(df_map))
                st.map(df_map[["lat", "lon"]], zoom=14)
        else:
            st.info("Sin vehiculos activos")

    with col_alertas:
        st.subheader("🔔 Anomalias")
        anomalias = _api_get("/v1/anomalias")
        if anomalias and anomalias.get("anomalias"):
            for a in anomalias["anomalias"][:6]:
                sev = a.get("severidad", "media")
                st.markdown(f"<div class='alert-card alert-{sev}'>{a['descripcion']}</div>", unsafe_allow_html=True)
        else:
            st.info("Sin anomalias detectadas")

    st.divider()
    zonas_ocup = _api_get("/v1/zonas/ocupacion") or {}
    zonas_list = zonas_ocup.get("zonas", [])
    if zonas_list:
        st.subheader("📊 Ocupacion por Zona")
        cols_z = st.columns(len(zonas_list))
        for i, z in enumerate(zonas_list):
            cap = z.get("capacidad_maxima", 1) or 1
            pct = z.get("ocupados", 0) / cap * 100
            color = "#ef4444" if pct > 80 else "#eab308" if pct > 50 else "#22c55e"
            cols_z[i].metric(
                f"📍 {z['nombre']}", f"{z.get('ocupados', 0)}/{cap}",
                f"{pct:.0f}%", delta_color="off",
            )

    st.divider()
    analiticas = _api_get("/v1/analiticas/estadisticas", {"desde": (datetime.now(UTC) - timedelta(30)).strftime("%Y-%m-%d"), "hasta": datetime.now(UTC).strftime("%Y-%m-%d"), "agrupacion": "dia"})
    if analiticas and analiticas.get("serie_temporal"):
        st.subheader("📈 Tendencias 30 dias")
        df_s = pd.DataFrame(analiticas["serie_temporal"])
        if not df_s.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_s["periodo"], y=df_s["recaudacion"], mode="lines+markers", name="Recaudacion", line={"color": "#00b1ea"}, fill="tozeroy", fillcolor="rgba(0,177,234,0.1)"))
            fig.update_layout(margin={"t": 20, "b": 20, "l": 20, "r": 20}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"color": "white"}, height=300)
            st.plotly_chart(fig, use_container_width=True)
            ca, cb, cc = st.columns(3)
            ca.metric("Total Estacionamientos", analiticas["total_estacionamientos"])
            cb.metric("Recaudacion Total", f"${analiticas['recaudacion_total']:,.0f}")
            cc.metric("Duracion Promedio", f"{analiticas['duracion_promedio_minutos']:.0f} min")

    st.divider()
    col_pie, col_radar = st.columns(2)
    with col_pie:
        st.subheader("📊 Metodos de Pago")
        if df is not None and total_pagos > 0:
            df_p = df[(df["estado"] == "finalizado") & (df["metodo_pago"].notna()) & (df["metodo_pago"] != "")]
            conteo = df_p["metodo_pago"].value_counts().reset_index()
            conteo.columns = ["Metodo", "Cantidad"]
            fig = px.pie(conteo, values="Cantidad", names="Metodo", hole=0.5, color_discrete_sequence=["#00b1ea", "#85bb65"])
            fig.update_layout(margin={"t": 20, "b": 20}, paper_bgcolor="rgba(0,0,0,0)", font={"color": "white"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos")

    with col_radar:
        st.subheader("📡 Radar Activo")
        if not df_activos.empty:
            tabla = df_activos[["patente", "hora_inicio", "legajo_permisionario"]].copy()
            tabla["hora_inicio"] = pd.to_datetime(tabla["hora_inicio"]).dt.strftime("%H:%M")
            tabla.columns = ["Patente", "Entrada", "Permisionario"]
            st.dataframe(tabla, use_container_width=True, hide_index=True, height=350)
        else:
            st.info("Sin vehiculos activos")

    st.divider()
    st.subheader("🤖 Intendente AI")
    if "ia_report" not in st.session_state:
        st.session_state.ia_report = None
        
    if st.button("Generar Reporte IA", key="ia_btn"):
        if not GEMINI_API_KEY:
            st.error(f"GEMINI_API_KEY no encontrada. Ruta .env buscada: {_ENV_PATH}")
        elif _GENAI_SDK is None:
            st.error("Libreria Gemini no instalada. Ejecuta: pip install google-genai")
        else:
            with st.spinner("Generando reporte con Gemini (esto puede tardar unos segundos)..."):
                try:
                    prompt = (f"SEM Salta: {vehiculos_activos} activos, ${recaudacion_hoy:,.0f} recaudado, "
                              f"{porcentaje_digital:.0f}% digital, {pendientes_multas} multas pendientes. "
                              f"Reporte ejecutivo 1 parrafo para el Intendente con accion recomendada.")
                    if _GENAI_SDK == "new":
                        client = _genai_new.Client(api_key=GEMINI_API_KEY)
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=prompt,
                        )
                        st.session_state.ia_report = response.text
                    else:
                        _genai_legacy.configure(api_key=GEMINI_API_KEY)
                        model = _genai_legacy.GenerativeModel("gemini-2.0-flash")
                        response = model.generate_content(prompt)
                        st.session_state.ia_report = response.text
                except Exception as e:
                    err = str(e)
                    if "not found" in err.lower() or "404" in err:
                        st.warning("Modelo Gemini no disponible. Probablemente la API key no tiene acceso a ese modelo. Usa gemini-2.0-flash en Google AI Studio.")
                    elif "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                        st.warning("Gemini: cuota gratuita agotada. Reintenta en unos minutos o usa otra API key.")
                    else:
                        st.error(f"Error Gemini: {err[:200]}")

    if st.session_state.ia_report:
        st.success("Reporte generado:")
        st.info(st.session_state.ia_report)

# ── TAB 2: Vehiculos ──
with t2:
    st.subheader("🔍 Busqueda de Vehiculo")
    patente_buscar = st.text_input("Patente", key="v_pat").upper()
    if st.button("🔍 Buscar Historial") and patente_buscar:
        hist = _api_get(f"/v1/vehiculos/{patente_buscar}/historial")
        if hist:
            t = hist.get("totales", {})
            e = hist.get("estadisticas", {})
            a = hist.get("abono_activo")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Gastado", f"${t.get('total_gastado', 0):,.0f}")
            c2.metric("Estacionamientos", t.get("total_estacionamientos", 0))
            c3.metric("Multas Pendientes", f"${t.get('total_pendiente_multas', 0):,.0f}")

            c4, c5, c6 = st.columns(3)
            c4.metric("Zona Favorita", str(e.get("zona_favorita", "N/A")))
            c5.metric("Duracion Prom.", f"{e.get('duracion_promedio_min', 0):.0f}min")
            c6.metric("Metodo Preferido", str(e.get("metodo_pago_favorito", "N/A")))

            if a:
                st.success(f"Abono activo hasta {a.get('fecha_fin', 'N/A')}")

            if hist.get("estacionamientos"):
                st.subheader("Estacionamientos")
                df_hist = pd.DataFrame(hist["estacionamientos"])[["hora_inicio", "hora_fin", "monto_final", "estado", "metodo_pago", "zona_id"]]
                st.dataframe(df_hist, use_container_width=True, hide_index=True)

            if hist.get("infracciones"):
                st.subheader("Infracciones")
                df_inf = pd.DataFrame(hist["infracciones"])[["tipo_infraccion", "monto_multa", "estado", "creado_en"]]
                st.dataframe(df_inf, use_container_width=True, hide_index=True)
        else:
            st.warning("Vehiculo no encontrado o sin datos")

    st.divider()
    st.subheader("📋 Prediccion de Demanda")
    pred = _api_get("/v1/anomalias/prediccion-demanda")
    if pred and pred.get("predicciones"):
        df_pred = pd.DataFrame(pred["predicciones"])
        if not df_pred.empty:
            fig = px.density_heatmap(df_pred, x="hora", y="zona_id", z="demanda_promedio", color_continuous_scale="Blues", title="Demanda por Hora y Zona")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={"color": "white"}, height=350)
            st.plotly_chart(fig, use_container_width=True)

# ── TAB 3: Infracciones ──
with t3:
    infracciones = cargar_datos_infracciones()
    if infracciones:
        st.subheader(f"🚨 Infracciones ({len(infracciones)})")
        df_inf = pd.DataFrame(infracciones)
        cols_show = ["patente", "tipo_infraccion", "monto_multa", "estado", "creado_en"]
        df_inf_show = df_inf[[c for c in cols_show if c in df_inf.columns]]
        st.dataframe(df_inf_show, use_container_width=True, hide_index=True)

        apelaciones = [i for i in infracciones if i.get("apelacion_estado") == "pendiente_revision"]
        if apelaciones:
            st.subheader(f"📝 Apelaciones Pendientes ({len(apelaciones)})")
            for a in apelaciones:
                with st.expander(f"{a['patente']} - {a.get('tipo_infraccion')} - ${a.get('monto_multa', 0)}"):
                    st.text(a.get("apelacion_texto", "Sin texto"))
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Aceptar", key=f"acc_{a['id']}"):
                        _api_post(f"/v1/infracciones/{a['id']}/resolver-apelacion", {"decision": "aceptada", "respuesta": "Apelacion aceptada"})
                        st.rerun()
                    if c2.button("❌ Rechazar", key=f"rej_{a['id']}"):
                        _api_post(f"/v1/infracciones/{a['id']}/resolver-apelacion", {"decision": "rechazada", "respuesta": "Apelacion rechazada"})
                        st.rerun()

        total_pend = sum(i["monto_multa"] for i in infracciones if i.get("estado") == "pendiente")
        st.metric("Total Pendiente Cobro", f"${total_pend:,.0f}")
    else:
        st.info("Sin infracciones registradas")

# ── TAB 4: Administracion ──
with t4:
    admin_subtab = st.selectbox("Seccion", ["Inspectores", "Zonas", "Tarifas", "Cierre Diario", "Digest Email"])

    if admin_subtab == "Inspectores":
        st.subheader("👮 Inspectores")
        inspectores = cargar_inspectores()
        if inspectores and inspectores.get("inspectores"):
            df_ins = pd.DataFrame(inspectores["inspectores"])
            cols = ["legajo", "nombre", "rol", "activo"]
            st.dataframe(df_ins[[c for c in cols if c in df_ins.columns]], use_container_width=True, hide_index=True)

        with st.expander("➕ Crear Inspector"):
            with st.form("form_crear_ins"):
                leg = st.text_input("Legajo")
                nom = st.text_input("Nombre")
                pw = st.text_input("Password", type="password")
                rol = st.selectbox("Rol", ["inspector", "supervisor", "admin"])
                if st.form_submit_button("Crear"):
                    res = _api_post("/v1/admin/inspectores", {"legajo": leg, "nombre": nom, "password": pw, "rol": rol})
                    if "error" in res:
                        st.error(f"{res.get('error')} (URL: {res.get('url', API_URL + '/v1/admin/inspectores')})")
                    else:
                        st.success("Inspector creado")
                        st.rerun()

    elif admin_subtab == "Zonas":
        st.subheader("📍 Zonas")
        zonas = _api_get("/v1/zonas")
        if zonas and zonas.get("zonas"):
            df_z = pd.DataFrame(zonas["zonas"])
            st.dataframe(df_z, use_container_width=True, hide_index=True)

    elif admin_subtab == "Tarifas":
        st.subheader("💲 Tarifas Especiales")
        tarifas = _api_get("/v1/tarifas/activas")
        if tarifas and tarifas.get("tarifas"):
            st.dataframe(pd.DataFrame(tarifas["tarifas"]), use_container_width=True, hide_index=True)
        else:
            st.info("Sin tarifas especiales activas")

        with st.expander("➕ Nueva Tarifa"):
            with st.form("form_tarifa"):
                ev = st.text_input("Nombre Evento")
                desde = st.date_input("Desde")
                hasta = st.date_input("Hasta")
                mult = st.number_input("Multiplicador", 1.0, 5.0, 1.5, 0.1)
                if st.form_submit_button("Crear"):
                    res = _api_post("/v1/tarifas/especiales", {"nombre_evento": ev, "fecha_inicio": str(desde), "fecha_fin": str(hasta), "multiplicador": mult})
                    if "error" in res:
                        st.error("Error al crear")
                    else:
                        st.success("Tarifa creada")

    elif admin_subtab == "Cierre Diario":
        st.subheader("⚙️ Cierre Diario")
        if st.button("⚠️ Ejecutar Cierre Diario Forzado"):
            res = _api_post("/v1/cierre_diario_forzado", {})
            if "error" in res:
                st.error("Error")
            else:
                st.success("Cierre ejecutado")
                st.rerun()

    elif admin_subtab == "Digest Email":
        st.subheader("📧 Reportes por Email")
        with st.form("form_digest"):
            email = st.text_input("Email")
            nombre = st.text_input("Nombre")
            frec = st.selectbox("Frecuencia", ["semanal", "mensual"])
            if st.form_submit_button("Suscribir"):
                res = _api_post("/v1/admin/digest/suscribir", {"email": email, "nombre": nombre, "frecuencia": frec})
                if "error" in res:
                    st.error(res.get("error", "Error"))
                else:
                    st.success("Suscripto!")

# ── TAB 5: Auditoria ──
with t5:
    st.subheader("📋 Registro de Actividad")
    col_f1, col_f2 = st.columns(2)
    legajo_filtro = col_f1.text_input("Filtrar por Legajo")
    if col_f2.button("🔍 Buscar"):
        pass

    aud = cargar_auditoria(legajo_filtro)
    if aud and aud.get("registros"):
        df_aud = pd.DataFrame(aud["registros"])
        cols = ["legajo_inspector", "accion", "entidad", "creado_en"]
        st.dataframe(df_aud[[c for c in cols if c in df_aud.columns]], use_container_width=True, hide_index=True, height=400)
        st.metric("Total Acciones Registradas", len(aud["registros"]))
    else:
        st.info("Sin registros de auditoria")
