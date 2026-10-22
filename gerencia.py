import streamlit as st
import pandas as pd
from supabase import create_client

# Configuración de la página para Gerencia
st.set_page_config(
    page_title="crealag - Resumen Gerencial", 
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
    except Exception:
        return None

supabase = init_supabase()

# Estilos CSS
css_estilos = """
<style>
.stApp { background-color: #0A0F1D; color: #F8FAFC; }
div[data-baseweb="select"] { background-color: #1A263D !important; color: #F8FAFC !important; border-color: #334155 !important; }
.brand-title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800; color: #F8FAFC; }
[data-testid="stMetricValue"] { color: #F8FAFC !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-weight: 700 !important; }
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
        return ["HC-0505"]
    try:
        res = supabase.table("Órdenes_Compra").select("orden_compra").execute()
        if res.data:
            return [row["orden_compra"] for row in res.data]
    except Exception:
        pass
    return ["HC-0505"]

# --- VISTA GERENCIAL ---
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Resumen Gerencial Diario</span></h1>", unsafe_allow_html=True)
st.markdown("---")

df = cargar_datos_supabase()
lista_ocs = cargar_catalogo_ocs()

oc_actual = st.selectbox("Seleccionar Orden de Compra:", lista_ocs)
st.markdown("---")

if not df.empty:
    df_oc = df[df["orden_compra"] == oc_actual]
    
    # Identificar registros con observaciones reales (para el contador de incidencias)
    df_obs = df_oc[
        df_oc["observaciones_turno"].notnull() & 
        (~df_oc["observaciones_turno"].str.strip().str.lower().isin(["sin observaciones", "sin observacion", ""]))
    ].copy()
    
    total_incidencias = len(df_obs)
    total_piezas_oc = df_oc["piezas_producidas"].sum() if not df_oc.empty else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Orden Activa", oc_actual)
    col2.metric("Total Producido", f"{total_piezas_oc} pzas")
    col3.metric("Reportes / Incidencias", f"{total_incidencias}")
    
    st.markdown("---")
    st.subheader(f"📅 Bitácora Resumida Diaria - {oc_actual}")
    
    # Obtener TODAS las fechas registradas en la orden (ordenadas de la más reciente a la más antigua)
    fechas_todas = sorted(df_oc["fecha"].astype(str).unique(), reverse=True)
    
    if fechas_todas:
        for f in fechas_todas:
            # Todos los registros de esta fecha para sumar la producción total del día
            df_todos_dia = df_oc[df_oc["fecha"].astype(str) == f]
            piezas_dia = df_todos_dia["piezas_producidas"].sum()
            
            # Filtrar solo las observaciones reales de ese día (excluyendo "Sin observaciones")
            df_obs_dia = df_todos_dia[
                df_todos_dia["observaciones_turno"].notnull() & 
                (~df_todos_dia["observaciones_turno"].str.strip().str.lower().isin(["sin observaciones", "sin observacion", ""]))
            ]
            
            if not df_obs_dia.empty:
                notas_resumidas = " | ".join(df_obs_dia["observaciones_turno"].tolist())
            else:
                notas_resumidas = "Operación normal (Sin incidencias reportadas)"
            
            st.markdown(f"""
            <div style="background-color: #111B2E; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 12px;">
                <div style="font-size: 16px; font-weight: bold; color: #F8FAFC; margin-bottom: 4px;">📅 Fecha: {f}</div>
                <div style="color: #94A3B8; font-size: 14px; margin-bottom: 4px;">📦 Producción total del día: <b style="color: #F8FAFC;">{piezas_dia} pzas</b></div>
                <div style="color: #E2E8F0; font-size: 14px;">📝 <b>Motivo / Novedades:</b> {notas_resumidas}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("🎉 No hay registros de producción para esta orden.")
else:
    st.info("Aún no hay registros en la base de datos.")