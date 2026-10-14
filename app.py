import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO
import os
from supabase import create_client
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración de la página con la identidad corporativa de Crealag
st.set_page_config(
    page_title="crealag - Control de Producción y Remisiones", 
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
    .stButton>button {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #F8FAFC;
        border: 1px solid #D4AF37;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        border-color: #FACC15;
        color: #FACC15;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.4);
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
            return df_cfg
    return pd.DataFrame([{"Orden_Compra": "HER-080526", "Meta_Piezas": 100}])

def guardar_catalogo_ocs(df_cfg):
    df_cfg.to_csv(CONFIG_FILE, index=False)

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

def insertar_registro(orden, fecha, hora, piezas, observaciones):
    try:
        nuevo = {
            "orden_compra": orden,
            "fecha": fecha,
            "hora": hora,
            "piezas_producidas": int(piezas),
            "observaciones_turno": observaciones
        }
        supabase.table("Producción").insert(nuevo).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar en la nube: {e}")
        return False

df = cargar_datos_supabase()

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 class='brand-title' style='color: #D4AF37; margin-bottom: 0px;'>crealag</h2>", unsafe_allow_html=True)
    st.caption("Fabricante mueblerio metalformado A.C. e INOX")
    st.markdown("---")
    
    menu_seleccionado = st.selectbox(
        "Navegación del Sistema",
        ["📊 Producción y Registro", "📄 Generador de Remisiones"]
    )
    
    st.markdown("---")
    st.header("📦 Órdenes de Compra")
    
    lista_ocs = df_ocs_catalogo["Orden_Compra"].tolist()
    oc_actual = st.selectbox("Seleccionar OC Activa:", lista_ocs)
    
    meta_actual = int(df_ocs_catalogo[df_ocs_catalogo["Orden_Compra"] == oc_actual]["Meta_Piezas"].values[0])
    
    with st.expander("➕ Registrar Nueva Orden de Compra"):
        nueva_oc_input = st.text_input("Nueva OC (Ej. HER-101026)")
        nueva_meta_input = st.number_input("Meta de piezas:", min_value=1, value=100, step=10)
        
        if st.button("Guardar Nueva OC"):
            if nueva_oc_input and nueva_oc_input not in lista_ocs:
                nuevo_row = pd.DataFrame([{"Orden_Compra": nueva_oc_input, "Meta_Piezas": nueva_meta_input}])
                df_ocs_catalogo = pd.concat([df_ocs_catalogo, nuevo_row], ignore_index=True)
                guardar_catalogo_ocs(df_ocs_catalogo)
                st.success(f"✅ OC `{nueva_oc_input}` registrada.")
                st.rerun()
            elif nueva_oc_input in lista_ocs:
                st.warning("Esta Orden de Compra ya existe en el catálogo.")

# Título principal
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Control de Producción y Remisiones</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# --- SECCIÓN 1: REGISTRO Y CONTROL DE PRODUCCIÓN ---
if menu_seleccionado == "📊 Producción y Registro":
    df_oc = df[df["orden_compra"] == oc_actual] if not df.empty and "orden_compra" in df.columns else pd.DataFrame()
    piezas_producidas_oc = df_oc["piezas_producidas"].sum() if not df_oc.empty else 0
    porcentaje = min(1.0, piezas_producidas_oc / meta_actual) if meta_actual > 0 else 0.0

    st.subheader(f"Panel de Control - Orden Activa: `{oc_actual}`")

    m1, m2, m3 = st.columns(3)
    m1.metric("OC Activa", oc_actual)
    m2.metric("Producidas / Meta", f"{piezas_producidas_oc} / {meta_actual}")
    m3.metric("Avance", f"{int(porcentaje * 100)}%")

    st.progress(porcentaje)

    if piezas_producidas_oc >= meta_actual and meta