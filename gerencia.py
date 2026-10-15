import streamlit as st
import pandas as pd
from datetime import datetime
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
    .welcome-card {
        background: linear-gradient(135deg, #111B2E 0%, #1A263D 100%);
        border: 1px solid #2D3E5E;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

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

# --- CARGAR ÓRDENES DE COMPRA DIRECTAMENTE DE LA NUBE ---
if not df_produccion.empty and "orden_compra" in df_produccion.columns:
    lista_ocs = df_produccion["orden_compra"].unique().tolist()
else:
    lista_ocs = ["HER-080526"]

# Inicializar el estado de la sesión para controlar si ya se seleccionó una orden
if "orden_seleccionada" not in st.session_state:
    st.session_state.orden_seleccionada = None

# --- BARRA LATERAL (SIMPLE) ---
with st.sidebar:
    st.markdown("<h2 class='brand-title' style='color: #D4AF37; margin-bottom: 0px;'>crealag</h2>", unsafe_allow_html=True)
    st.caption("Panel de Supervisión")
    st.markdown("---")
    st.success("🔒 **Solo Lectura**")
    st.markdown("---")
    
    if st.session_state.orden_seleccionada:
        if st.button("🔄 Cambiar de Orden de Compra", use_container_width=True):
            st.session_state.orden_seleccionada = None
            st.rerun()
            
    st.markdown("---")
    st.info("ℹ️ Este panel muestra el estado actual de la producción y el almacén en tiempo real.")

# --- PANTALLA 1: BIENVENIDA Y SELECCIÓN INICIAL ---
if st.session_state.orden_seleccionada is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="welcome-card">
                <h1 class="brand-title" style="color: #D4AF37; font-size: 36px; margin-bottom: 10px;">crealag</h1>
                <h3 style="color: #F8FAFC; font-weight: 400; margin-bottom: 20px;">Sistema de Supervisión</h3>
                <p style="color: #94A3B8; font-size: 15px;">Bienvenido al portal de control. Por favor, seleccione la Orden de Compra que desea monitorear para visualizar los datos en tiempo real.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("form_bienvenida"):
            oc_elegida = st.selectbox("Seleccione una Orden de Compra:", lista_ocs)
            st.markdown("<br>", unsafe_allow_html=True)
            btn_continuar = st.form_submit_button("Consultar Orden de Compra", use_container_width=True, type="primary")
            
        if btn_continuar:
            st.session_state.orden_seleccionada = oc_elegida
            st.rerun()

# --- PANTALLA 2: VISUALIZACIÓN DE DATOS DE LA ORDEN SELECCIONADA ---
else:
    oc_actual = st.session_state.orden_seleccionada
    
    # Título principal
    st.markdown(f"<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Orden de Compra: <b>{oc_actual}</b></span></h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Filtrar registros de la OC seleccionada
    df_oc_prod = df_produccion[df_produccion["orden_compra"] == oc_actual] if not df_produccion.empty and "orden_compra" in df_produccion.columns else pd.DataFrame()
    total_producido = int(df_oc_prod["piezas_producidas"].sum()) if not df_oc_prod.empty else 0

    # Meta estimada estándar
    meta_oc = 100 
    piezas_en_almacen = total_producido

    # Estado de la orden
    if total_producido >= meta_oc:
        st.success(f"🟢 **ESTADO DE LA ORDEN:** ¡TERMINADA! Se alcanzó o superó la meta de {meta_oc} piezas.")
    else:
        st.warning(f"🟡 **ESTADO DE LA ORDEN:** EN PROCESO (Faltan {max(0, meta_oc - total_producido)} piezas para completar la meta estimada).")

    # Métricas claras en pantalla grande
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Meta Estimada OC", f"{meta_oc} pzas")
    m2.metric("Producido Total", f"{total_producido} pzas")
    m3.metric("Entregadas / Remitidas", "0 pzas")
    m4.metric("Disponibles en Almacén", f"{piezas_en_almacen} pzas")

    porcentaje = min(1.0, total_producido / meta_oc) if meta_oc > 0 else 0.0
    st.progress(porcentaje)

    st.markdown("---")

    # HISTORIAL DE REGISTROS
    st.markdown(f"### 📑 Historial de Fabricación - `{oc_actual}`")
    if not df_oc_prod.empty:
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