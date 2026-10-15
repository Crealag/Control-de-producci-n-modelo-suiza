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
    div[data-baseweb="select"] {
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

# --- BARRA LATERAL (SIMPLE) ---
with st.sidebar:
    st.markdown("<h2 class='brand-title' style='color: #D4AF37; margin-bottom: 0px;'>crealag</h2>", unsafe_allow_html=True)
    st.caption("Panel Ejecutivo y Supervisión")
    st.markdown("---")
    st.success("🔒 **Solo Lectura**")
    st.markdown("---")
    st.info("ℹ️ Este panel muestra el estado actual de las órdenes de compra y el almacén en tiempo real.")

# Título principal
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Panel de Órdenes y Almacén</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# --- SECCIÓN PRINCIPAL: SELECCIÓN DIRECTA DE OC ---
lista_ocs = df_ocs_catalogo["Orden_Compra"].tolist()

st.markdown("### 📋 Seleccione la Orden de Compra que desea consultar:")
oc_actual = st.selectbox("", lista_ocs, label_visibility="collapsed")

# Obtener datos de la OC seleccionada
row_oc = df_ocs_catalogo[df_ocs_catalogo["Orden_Compra"] == oc_actual].iloc[0]
meta_oc = int(row_oc["Meta_Piezas"])

# Calcular producción total y piezas disponibles en almacén
df_oc_prod = df_produccion[df_produccion["orden_compra"] == oc_actual] if not df_produccion.empty and "orden_compra" in df_produccion.columns else pd.DataFrame()
total_producido = int(df_oc_prod["piezas_producidas"].sum()) if not df_oc_prod.empty else 0
piezas_entregadas_previas = int(row_oc["Piezas_Entregadas"]) if "Piezas_Entregadas" in row_oc else 0
piezas_en_almacen = max(0, total_producido - piezas_entregadas_previas)

st.markdown("---")

# Estado de la orden
if total_producido >= meta_oc:
    st.success(f"🟢 **ESTADO DE LA ORDEN `{oc_actual}`:** ¡TERMINADA! Se alcanzó o superó la meta de {meta_oc} piezas.")
else:
    st.warning(f"🟡 **ESTADO DE LA ORDEN `{oc_actual}`:** EN PROCESO (Faltan {meta_oc - total_producido} piezas para completar la meta).")

# Métricas claras en pantalla grande
m1, m2, m3, m4 = st.columns(4)
m1.metric("Meta de la OC", f"{meta_oc} pzas")
m2.metric("Producido Total", f"{total_producido} pzas")
m3.metric("Entregadas / Remitidas", f"{piezas_entregadas_previas} pzas")
m4.metric("Disponibles en Almacén", f"{piezas_en_almacen} pzas")

porcentaje = min(1.0, total_producido / meta_oc) if meta_oc > 0 else 0.0
st.progress(porcentaje)

st.markdown("---")

# HISTORIAL DE REGISTROS
st.markdown(f"### 📑 Historial de Fabricación - `{oc_actual}`")
if not df_oc_prod.empty:
    # Renombrar columnas para que se vean más amigables a la vista de los jefes
    df_mostrar = df_oc_prod.sort_values(by="id", ascending=False)[["fecha", "hora", "piezas_producidas", "observaciones_turno"]]
    df_mostrar.columns = ["Fecha", "Hora", "Piezas Producidas", "Observaciones del Turno"]
    st.dataframe(df_mostrar, use_container_width=True)
    
    csv_reporte_gen = df_oc_prod.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte de esta Orden (CSV)",
        data=csv_reporte_gen,
        file_name=f"Reporte_Gerencial_{oc_actual}.csv",
        mime="text/csv"
    )
else:
    st.info("Aún no hay registros de producción para esta orden en la base de datos.")