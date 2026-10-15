import streamlit as st
import pandas as pd
from datetime import datetime
import os
from supabase import create_client

# Configuración de la página con la identidad corporativa de Crealag (Panel Gerencial)
st.set_page_config(
    page_title="crealag - Panel Gerencial y Supervisión", 
    layout="wide", 
    page_icon="🏢"
)

# --- CREDENCIALES DE SUPABASE ---
SUPABASE_URL = "https://jdihosehcvvzxsbhnqvf.supabase.co"
SUPABASE_KEY = "sb_publishable_D79R2pyWt6LI3lggygrbjg_4oJmoEX_"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Estilos CSS con paleta Crealag
st.markdown("""
    <style>
    .stApp {
        background-color: #0A0F1D;
        color: #F8FAFC;
    }
    [data-testid="stSidebar"] {
        background-color: #111B2E;
    }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
        background-color: #1A263D !important;
        color: #F8FAFC !important;
        border-color: #2D3E5E !important;
    }
    .brand-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        color: #F8FAFC;
    }
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 0.8rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Archivo de configuración local para el catálogo de Órdenes de Compra
CONFIG_FILE = "oc_catalogo.csv"

def cargar_catalogo_ocs():
    if os.path.exists(CONFIG_FILE):
        df_cfg = pd.read_csv(CONFIG_FILE)
        if not df_cfg.empty:
            if "Estado" not in df_cfg.columns:
                df_cfg["Estado"] = "Activa"
            if "Piezas_Entregadas" not in df_cfg.columns:
                df_cfg["Piezas_Entregadas"] = 0
            return df_cfg
    return pd.DataFrame([{"Orden_Compra": "HER-080526", "Meta_Piezas": 100, "Estado": "Activa", "Piezas_Entregadas": 0}])

df_ocs_catalogo = cargar_catalogo_ocs()

# --- FUNCIONES DE BASE DE DATOS (SUPABASE) ---
def cargar_datos_supabase():
    try:
        response = supabase.table("Producción").select("*").execute()
        data = response.data
        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])

df_produccion = cargar_datos_supabase()

# --- BARRA LATERAL (SOLO CONSULTA) ---
with st.sidebar:
    st.markdown("<h2 class='brand-title' style='color: #D4AF37; margin-bottom: 0px;'>crealag</h2>", unsafe_allow_html=True)
    st.caption("Panel Ejecutivo y Supervisor")
    st.markdown("---")
    
    st.success("🔒 **Modo Gerencial de Solo Lectura**")
    st.markdown("---")
    
    st.header("📦 Órdenes de Compra")
    
    lista_ocs = df_ocs_catalogo["Orden_Compra"].tolist()
    oc_actual = st.selectbox("Seleccionar Orden:", lista_ocs)
    
    row_oc = df_ocs_catalogo[df_ocs_catalogo["Orden_Compra"] == oc_actual].iloc[0]
    meta_oc = int(row_oc["Meta_Piezas"])
    
    st.markdown("---")
    st.info("ℹ️ Este panel es exclusivamente para consulta de avance, estado de órdenes y control de almacén.")

# Título principal
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Panel Gerencial de Supervisión</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# Calcular producción total y piezas disponibles en almacén para la OC seleccionada
df_oc_prod = df_produccion[df_produccion["orden_compra"] == oc_actual] if not df_produccion.empty and "orden_compra" in df_produccion.columns else pd.DataFrame()
total_producido = int(df_oc_prod["piezas_producidas"].sum()) if not df_oc_prod.empty else 0
piezas_entregadas_previas = int(row_oc["Piezas_Entregadas"]) if "Piezas_Entregadas" in row_oc else 0
piezas_en_almacen = max(0, total_producido - piezas_entregadas_previas)

# --- TABLERO Y ESTADO DE ALMACÉN ---
st.subheader(f"Monitoreo de Orden: `{oc_actual}`")

if total_producido >= meta_oc:
    st.success(f"🟢 **ESTADO DE LA ORDEN:** ¡TERMINADA! Se alcanzó o superó la meta de {meta_oc} piezas.")
else:
    st.warning(f"🟡 **ESTADO DE LA ORDEN:** En proceso (Faltan {meta_oc - total_producido} piezas para la meta).")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Meta de la OC", f"{meta_oc} pzas")
m2.metric("Producido Total", f"{total_producido} pzas")
m3.metric("Entregadas / Remitidas", f"{piezas_entregadas_previas} pzas")
m4.metric("Disponibles en Almacén", f"{piezas_en_almacen} pzas")

porcentaje = min(1.0, total_producido / meta_oc) if meta_oc > 0 else 0.0
st.progress(porcentaje)
st.markdown("---")

# HISTORIAL DE PRODUCCIÓN
st.subheader(f"📋 Historial de Producción en Nube - {oc_actual}")
if not df_oc_prod.empty:
    st.dataframe(df_oc_prod.sort_values(by="id", ascending=False), use_container_width=True)
    csv_reporte_gen = df_oc_prod.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte en CSV",
        data=csv_reporte_gen,
        file_name=f"Reporte_Gerencial_{oc_actual}.csv",
        mime="text/csv"
    )
else:
    st.info("No hay registros de producción disponibles para esta orden.")

st.markdown("---")

# GRÁFICAS EJECUTIVAS
st.subheader("📈 Análisis de Rendimiento")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("##### 🕒 Ritmo por Hora (Hoy)")
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    df_hoy = df_produccion[df_produccion["fecha"] == hoy_str] if not df_produccion.empty and "fecha" in df_produccion.columns else pd.DataFrame()

    if not df_hoy.empty:
        df_h = df_hoy.copy()
        df_h['Hora_Int'] = pd.to_datetime(df_h['hora'], format='%H:%M:%S', errors='coerce').dt.hour
        df_h = df_h[(df_h['Hora_Int'] >= 8) & (df_h['Hora_Int'] <= 18) & (df_h['Hora_Int'] != 13)]
        
        if not df_h.empty:
            df_h['Rango_Hora'] = df_h['Hora_Int'].apply(lambda x: f"{x:02d}:00 - {x+1:02d}:00")
            df_por_hora = df_h.groupby('Rango_Hora')['piezas_producidas'].sum()
            horas_jornada = [f"{h:02d}:00 - {h+1:02d}:00" for h in [8,9,10,11,12,14,15,16,17]]
            df_por_hora = df_por_hora.reindex(horas_jornada, fill_value=0)
            st.bar_chart(df_por_hora)
        else:
            st.info("💡 Sin registros en horario laboral hoy.")
    else:
        st.info("💡 Sin registros para el día de hoy.")

with col_g2:
    st.markdown(f"##### 📅 Producción Acumulada por Día")
    if not df_oc_prod.empty:
        df_dias = df_oc_prod.copy()
        df_por_dia = df_dias.groupby('fecha')['piezas_producidas'].sum()
        st.line_chart(df_por_dia)
    else:
        st.info("💡 Sin registros diarios en esta orden.")