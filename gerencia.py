import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client

# Configuración de la página
st.set_page_config(
    page_title="crealag - Portal de Supervisión", 
    layout="wide", 
    page_icon="🏢"
)

# --- CREDENCIALES ---
SUPABASE_URL = "https://jdihosehcvvzxsbhnqvf.supabase.co"
SUPABASE_KEY = "sb_publishable_D79R2pyWt6LI3lggygrbjg_4oJmoEX_"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return None

supabase = init_supabase()

# --- ESTILOS CSS DE ALTA GAMA (UI/UX CENTRADO) ---
css_estilos = """
<style>
.stApp { background-color: #050811; color: #F8FAFC; font-family: 'Inter', sans-serif; }
div[data-baseweb="select"] { background-color: #0F172A !important; color: #F8FAFC !important; border-color: #334155 !important; border-radius: 10px; }
.brand-title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px; text-align: center; }

[data-testid="stMetricValue"] { color: #F8FAFC !important; font-weight: 800 !important; font-size: 1.8rem !important; }
[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-weight: 600 !important; font-size: 0.85rem !important; text-transform: uppercase; letter-spacing: 0.5px; }

/* Tarjetas ejecutivas con efecto flotante */
.exec-card {
    background: linear-gradient(145deg, #0F172A 0%, #1E293B 100%);
    padding: 28px;
    border-radius: 16px;
    border: 1px solid rgba(56, 189, 248, 0.15);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    margin-bottom: 25px;
}

/* Banner de Bienvenida Premium Centrado */
.welcome-hero {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0B132B 100%);
    padding: 40px;
    border-radius: 20px;
    border-top: 6px solid #38BDF8;
    border-left: 1px solid rgba(255,255,255,0.05);
    border-right: 1px solid rgba(255,255,255,0.05);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 25px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.4);
    text-align: center;
}

.selector-container {
    background: #0B132B;
    padding: 24px;
    border-radius: 14px;
    border: 1px solid #1E293B;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    margin-bottom: 30px;
}
</style>
"""
st.markdown(css_estilos, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
def cargar_datos_supabase():
    if not supabase:
        return pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])
    try:
        res = supabase.table("Producción").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])
    except Exception:
        return pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])

def cargar_catalogo_ocs():
    if not supabase:
        return pd.DataFrame([{"orden_compra": "HC-0505", "meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}])
    try:
        res = supabase.table("Órdenes_Compra").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame([{"orden_compra": "HC-0505", "meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}])

# --- ENCABEZADO SUPERIOR ACTUALIZADO ---
st.markdown("<h1 class='brand-title' style='font-size: 2.2rem;'>crealag <span style='font-weight: 300; font-size: 20px; color: #94A3B8;'>| Portal de Supervisión de Producción</span></h1>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #1E293B; margin-top: 12px; margin-bottom: 30px;'>", unsafe_allow_html=True)

df = cargar_datos_supabase()
df_ocs_catalogo = cargar_catalogo_ocs()
lista_ocs = df_ocs_catalogo["orden_compra"].tolist() if not df_ocs_catalogo.empty else ["HC-0505"]

# Gestionar estado en session_state para la orden seleccionada
if "oc_seleccionada" not in st.session_state:
    st.session_state.oc_seleccionada = "-- Selecciona una Orden de Compra --"

# Si no hay orden seleccionada, mostramos la bienvenida arriba y el selector abajo en columnas centradas
if st.session_state.oc_seleccionada == "-- Selecciona una Orden de Compra --":
    col1, col_centro, col3 = st.columns([1, 2.2, 1])
    with col_centro:
        # 1. Bienvenida Arriba
        st.markdown("""
        <div class="welcome-hero">
            <span style="background-color: rgba(56, 189, 248, 0.15); color: #38BDF8; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Panel de Supervisión</span>
            <h2 style="color: #F8FAFC; margin: 15px 0 10px 0; font-size: 1.8rem; font-weight: 700;">¡Bienvenido al Portal de Supervisión!</h2>
            <p style="color: #94A3B8; margin: 0; font-size: 0.95rem; line-height: 1.6;">
                Plataforma centralizada para el seguimiento en tiempo real del rendimiento de producción, inventario en almacén y bitácoras operativas de piso.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 2. Selector Abajo
        st.markdown("<div class='selector-container'>", unsafe_allow_html=True)
        st.markdown("<p style='color: #38BDF8; font-weight: 600; font-size: 0.95rem; margin-bottom: 8px; text-align: center;'>🎯 SELECCIONA LA ORDEN DE COMPRA A CONSULTAR</p>", unsafe_allow_html=True)
        
        def actualizar_seleccion():
            st.session_state.oc_seleccionada = st.session_state.widget_selector

        opciones_selector = ["-- Selecciona una Orden de Compra --"] + lista_ocs
        st.selectbox("", opciones_selector, key="widget_selector", on_change=actualizar_seleccion, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.stop()

# --- SI YA SE SELECCIONÓ UNA ORDEN: LA BIENVENIDA DESAPARECE Y SE MUESTRA EL CONTENIDO ---
oc_actual = st.session_state.oc_seleccionada

col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
with col_s2:
    opciones_selector = ["-- Selecciona una Orden de Compra --"] + lista_ocs
    nuevo_cambio = st.selectbox("Cambiar Orden de Compra:", opciones_selector, index=opciones_selector.index(oc_actual) if oc_actual in opciones_selector else 0, key="widget_cambio")
    if nuevo_cambio != "-- Selecciona una Orden de Compra --" and nuevo_cambio != oc_actual:
        st.session_state.oc_seleccionada = nuevo_cambio
        st.rerun()
    elif nuevo_cambio == "-- Selecciona una Orden de Compra --":
        st.session_state.oc_seleccionada = "-- Selecciona una Orden de Compra --"
        st.rerun()

st.markdown("<hr style='border-color: #1E293B; margin: 25px 0;'>", unsafe_allow_html=True)

try:
    row_oc_info = df_ocs_catalogo[df_ocs_catalogo["orden_compra"] == oc_actual].iloc[0]
    meta_actual = int(row_oc_info.get("meta_piezas", 1700))
    estado_oc = str(row_oc_info.get("estado", "Activa"))
    entregadas_actual = int(row_oc_info.get("piezas_entregadas", 0) if pd.notnull(row_oc_info.get("piezas_entregadas")) else 0)
except Exception:
    meta_actual = 1700
    estado_oc = "Activa"
    entregadas_actual = 0

if not df.empty and "orden_compra" in df.columns:
    df_oc = df[df["orden_compra"] == oc_actual].copy()
    
    total_piezas_oc = df_oc["piezas_producidas"].sum() if not df_oc.empty else 0
    piezas_almacen_actual = max(0, total_piezas_oc - entregadas_actual)
    porcentaje = min(1.0, total_piezas_oc / meta_actual) if meta_actual > 0 else 0.0
    
    # --- TARJETA CONTENEDORA DE MÉTRICAS ---
    st.markdown(f"""
    <div class="exec-card">
        <div style="font-size: 1.2rem; font-weight: 700; color: #38BDF8; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <span>📊 Estatus de Supervisión — Orden de Compra: {oc_actual}</span>
            <span style="font-size: 0.85rem; background-color: #0284C7; color: #F0F9FF; padding: 4px 12px; border-radius: 6px; font-weight: 600;">{estado_oc}</span>
        </div>
    """, unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Meta Estimada OC", f"{meta_actual:,} pzas")
    m2.metric("Producido Total", f"{total_piezas_oc:,} pzas")
    m3.metric("Entregadas / Remitidas", f"{entregadas_actual:,} pzas")
    m4.metric("Disponibles en Almacén", f"{piezas_almacen_actual:,} pzas")
    
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    st.progress(porcentaje)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not df_oc.empty:
        df_oc['fecha_dt'] = pd.to_datetime(df_oc['fecha'])
        
        # Calcular rangos de semana
        df_oc['inicio_semana'] = df_oc['fecha_dt'] - pd.to_timedelta(df_oc['fecha_dt'].dt.dayofweek, unit='d')
        df_oc['fin_semana'] = df_oc['inicio_semana'] + pd.to_timedelta(6, unit='d')
        
        df_oc['semana_label'] = (
            "Del " + df_