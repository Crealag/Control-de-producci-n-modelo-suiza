import streamlit as st
import pandas as pd
from supabase import create_client

# Configuración de la página para Gerencia
st.set_page_config(
    page_title="crealag - Resumen Gerencial", 
    layout="wide", 
    page_icon="🏢"
)

# --- CREDENCIALES (Mismas de tu sistema) ---
SUPABASE_URL = "https://jdihosehcvvzxsbhnqvf.supabase.co"
SUPABASE_KEY = "sb_publishable_D79R2pyWt6LI3lggygrbjg_4oJmoEX_"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = init_supabase()

# Estilos CSS - Paleta Oscura Neutra
css_estilos = """
<style>
.stApp { background-color: #0A0F1D; color: #F8FAFC; }
div[data-baseweb="select"] {
    background-color: #1A263D !important; color: #F8FAFC !important; border-color: #334155 !important;
}
.brand-title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800; color: #F8FAFC; }
[data-testid="stMetricValue"] { color: #F8FAFC !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-weight: 700 !important; }
</style>
"""
st.markdown(css_estilos, unsafe_allow_html=True)

# --- FUNCIÓN DE CARGA DE DATOS ---
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

# --- VISTA PRINCIPAL DE GERENCIA ---
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Portal Gerencial - Bitácora y Novedades</span></h1>", unsafe_allow_html=True)
st.markdown("---")

df = cargar_datos_supabase()
lista_ocs = cargar_catalogo_ocs()

# Selector de Orden de Compra en la parte superior
oc_actual = st.selectbox("Seleccionar Orden de Compra a Revisar:", lista_ocs)

st.markdown("---")

if not df.empty:
    df_oc = df[df["orden_compra"] == oc_actual]
    
    # Filtrar solo las observaciones reales (excluyendo "Sin observaciones")
    df_obs = df_oc[
        df_oc["observaciones_turno"].notnull() & 
        (~df_oc["observaciones_turno"].str.strip().str.lower().isin(["sin observaciones", "sin observacion", ""]))
    ].copy()
    
    total_reportes = len(df_obs)
    
    # Métricas informativas para gerencia
    col1, col2 = st.columns(2)
    col1.metric("Orden de Compra en Revisión", oc_actual)
    col2.metric("Total de Incidencias / Justificaciones", f"{total_reportes} reportes")
    
    st.markdown("---")
    st.subheader(f"📋 Resumen Diario de Observaciones - {oc_actual}")
    
    if not df_obs.empty:
        # Ordenar por fecha descendente
        fechas_unicas = sorted(df_obs["fecha"].astype(str).unique(), reverse=True)
        
        for f in fechas_unicas:
            st.markdown(f"### 📅 Fecha: `{f}`")
            df_dia = df_obs[df_obs["fecha"].astype(str) == f]
            
            for _, row in df_dia.iterrows():
                hora_txt = f" a las {row['hora']}" if pd.notnull(row['hora']) and str(row['hora']).strip() else ""
                st.info(f"📌 **{row['piezas_producidas']} pzas producidas**{hora_txt} — **Motivo:** {row['observaciones_turno']}")
            st.markdown("<br>", unsafe_allow_html=True)
            
        with st.expander("🔍 Ver Tabla Completa de Incidencias"):
            df_tabla_ger = df_obs[["fecha", "hora", "piezas_producidas", "observaciones_turno"]].sort_values(by="fecha", ascending=False)
            df_tabla_ger.columns = ["Fecha", "Hora", "Piezas Producidas", "Observación / Motivo"]
            st.dataframe(df_tabla_ger, use_container_width=True)
    else:
        st.success("🎉 No hay incidencias ni retrasos reportados para esta orden. Todos los registros se encuentran operando con normalidad.")
else:
    st.info("Aún no hay registros de producción en la base de datos.")