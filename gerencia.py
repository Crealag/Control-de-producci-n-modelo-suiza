import streamlit as st
import pandas as pd
from datetime import datetime, date
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
    except Exception as e:
        st.error(f"Error de conexión con Supabase: {e}")
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
    except Exception as e:
        return pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])

def cargar_catalogo_ocs():
    if not supabase:
        return pd.DataFrame([{"orden_compra": "HC-0505", "meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}])
    try:
        res = supabase.table("Órdenes_Compra").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        pass
    return pd.DataFrame([{"orden_compra": "HC-0505", "meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}])

# --- VISTA GERENCIAL ---
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Resumen Gerencial por Fechas</span></h1>", unsafe_allow_html=True)
st.markdown("---")

df = cargar_datos_supabase()
df_ocs_catalogo = cargar_catalogo_ocs()

lista_ocs = df_ocs_catalogo["orden_compra"].tolist() if not df_ocs_catalogo.empty else ["HC-0505"]
oc_actual = st.selectbox("Seleccionar Orden de Compra:", lista_ocs)

# Obtener datos de la OC seleccionada
try:
    row_oc_info = df_ocs_catalogo[df_ocs_catalogo["orden_compra"] == oc_actual].iloc[0]
    meta_actual = int(row_oc_info.get("meta_piezas", 1700))
    estado_oc = str(row_oc_info.get("estado", "Activa"))
    entregadas_actual = int(row_oc_info.get("piezas_entregadas", 0) if pd.notnull(row_oc_info.get("piezas_entregadas")) else 0)
except Exception:
    meta_actual = 1700
    estado_oc = "Activa"
    entregadas_actual = 0

st.markdown("---")

if not df.empty and "orden_compra" in df.columns:
    df_oc = df[df["orden_compra"] == oc_actual].copy()
    
    total_piezas_oc = df_oc["piezas_producidas"].sum() if not df_oc.empty else 0
    piezas_almacen_actual = max(0, total_piezas_oc - entregadas_actual)
    porcentaje = min(1.0, total_piezas_oc / meta_actual) if meta_actual > 0 else 0.0
    
    # --- MÉTRICAS Y BARRA DE PROGRESO ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Meta Estimada OC", f"{meta_actual} pzas")
    m2.metric("Producido Total", f"{total_piezas_oc} pzas")
    m3.metric("Entregadas / Remitidas", f"{entregadas_actual} pzas")
    m4.metric("Disponibles en Almacén", f"{piezas_almacen_actual} pzas")
    
    st.progress(porcentaje)
    st.markdown("---")
    
    if not df_oc.empty:
        df_oc['fecha_dt'] = pd.to_datetime(df_oc['fecha'])
        
        # Calcular el inicio (Lunes) y fin (Domingo) de cada semana automáticamente
        df_oc['inicio_semana'] = df_oc['fecha_dt'] - pd.to_timedelta(df_oc['fecha_dt'].dt.dayofweek, unit='d')
        df_oc['fin_semana'] = df_oc['inicio_semana'] + pd.to_timedelta(6, unit='d')
        
        # Crear etiqueta con rangos de fechas claros (Ej: "Del 19/10/2026 al 25/10/2026")
        df_oc['semana_label'] = (
            "Del " + df_oc['inicio_semana'].dt.strftime('%d/%m/%Y') + 
            " al " + df_oc['fin_semana'].dt.strftime('%d/%m/%Y')
        )
        
        # Detectar la semana actual para seleccionarla por defecto
        hoy = pd.Timestamp(date.today())
        inicio_hoy = hoy - pd.to_timedelta(hoy.dayofweek, unit='d')
        fin_hoy = inicio_hoy + pd.to_timedelta(6, unit='d')
        etiqueta_actual = f"Del {inicio_hoy.strftime('%d/%m/%Y')} al {fin_hoy.strftime('%d/%m/%Y')}"
        
        semanas_disponibles = sorted(df_oc['semana_label'].unique(), reverse=True)
        
        default_idx = 0
        if etiqueta_actual in semanas_disponibles:
            default_idx = semanas_disponibles.index(etiqueta_actual)
            
        st.subheader("📅 Filtrar Bitácora por Rango Semanal")
        semana_seleccionada = st.selectbox("Selecciona el rango de fechas a revisar:", semanas_disponibles, index=default_idx)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### 📋 Resumen del Periodo `{semana_seleccionada}` - {oc_actual} ({estado_oc})")
        
        df_semana = df_oc[df_oc['semana_label'] == semana_seleccionada]
        fechas_semana = sorted(df_semana["fecha"].astype(str).unique(), reverse=True)
        
        datos_tabla = []
        for f in fechas_semana:
            df_todos_dia = df_semana[df_semana["fecha"].astype(str) == f]
            piezas_dia = df_todos_dia["piezas_producidas"].sum()
            
            df_obs_dia = df_todos_dia[
                df_todos_dia["observaciones_turno"].notnull() & 
                (~df_todos_dia["observaciones_turno"].str.strip().str.lower().isin(["sin observaciones", "sin observacion", ""]))
            ]
            
            if not df_obs_dia.empty:
                notas_resumidas = " | ".join(df_obs_dia["observaciones_turno"].tolist())
            else:
                notas_resumidas = "Operación normal (Sin incidencias)"
            
            datos_tabla.append({
                "Fecha": f,
                "Producción Diaria": f"{piezas_dia} pzas",
                "Novedades / Motivo": notas_resumidas
            })
        
        df_resumen_gerencia = pd.DataFrame(datos_tabla)
        
        st.dataframe(
            df_resumen_gerencia, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Fecha": st.column_config.TextColumn("📅 Fecha", width="medium"),
                "Producción Diaria": st.column_config.TextColumn("📦 Producción del Día", width="medium"),
                "Novedades / Motivo": st.column_config.TextColumn("📝 Novedades / Motivos de Desviación", width="large"),
            }
        )
    else:
        st.success("🎉 No hay registros de producción para esta orden.")
else:
    st.info("Aún no hay registros en la base de datos.")