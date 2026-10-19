import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client

# Configuración de la página con la identidad corporativa de Crealag
st.set_page_config(
    page_title="crealag - Sistema de Supervisión", 
    layout="wide", 
    page_icon="🏢"
)

# --- CREDENCIALES ---
SUPABASE_URL = "https://jdihosehcvvzxsbhnqvf.supabase.co"
SUPABASE_KEY = "sb_publishable_D79R2pyWt6LI3lggygrbjg_4oJmoEX_"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Estilos CSS - Paleta Oscura Ejecutiva Crealag
css_estilos = """
<style>
.stApp, [data-testid="stHeader"], [data-testid="stToolbar"] {
    background-color: #0A0F1D !important;
    color: #F8FAFC !important;
}
[data-testid="stSidebar"] {
    background-color: #111B2E !important;
    border-right: 1px solid #1E293B !important;
}
h1, h2, h3, h4, h5, h6, p, span, label, div, .stMarkdown {
    color: #F8FAFC !important;
    font-weight: 700 !important;
}
div[data-baseweb="select"] > div {
    background-color: #1A263D !important;
    color: #F8FAFC !important;
    border: 1px solid #2D3E5E !important;
    border-radius: 8px !important;
}
[data-baseweb="popover"], [data-baseweb="menu"] {
    background-color: #111B2E !important;
    color: #F8FAFC !important;
}
button, .stButton > button, [data-testid="baseButton-primary"], div.stButton > button {
    background: linear-gradient(135deg, #2D2412 0%, #1A160A 100%) !important;
    color: #F8FAFC !important;
    border: 1px solid #D4AF37 !important;
    border-radius: 8px !important;
    font-size: 16px !important;
    font-weight: 800 !important;
    padding: 10px 20px !important;
}
[data-testid="stMetricValue"] {
    color: #F8FAFC !important;
    font-weight: 800 !important;
    font-size: 30px !important;
}
[data-testid="stMetricLabel"] {
    color: #94A3B8 !important;
    font-weight: 700 !important;
}
.brand-title {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-weight: 800 !important;
    color: #F8FAFC !important;
}
.welcome-card {
    background: #111B2E;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 40px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    margin-top: 30px;
}
</style>
"""
st.markdown(css_estilos, unsafe_allow_html=True)

# --- CARGAR DATOS ---
def cargar_catalogo_ocs():
    try:
        res = supabase.table("Órdenes_Compra").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(columns=["orden_compra", "meta_piezas", "estado", "piezas_entregadas"])

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

df_ocs_catalogo = cargar_catalogo_ocs()
df_produccion = cargar_datos_supabase()

lista_ocs = df_ocs_catalogo["orden_compra"].tolist() if not df_ocs_catalogo.empty else []

if "orden_seleccionada" not in st.session_state:
    st.session_state.orden_seleccionada = None

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 class='brand-title' style='color: #D4AF37 !important; margin-bottom: 0px;'>crealag</h2>", unsafe_allow_html=True)
    st.caption("Sistema de Supervisión")
    st.markdown("---")
    st.success("🔒 **Solo Lectura**")
    st.markdown("---")
    
    if st.session_state.orden_seleccionada:
        if st.button("🔄 Cambiar de Orden de Compra", use_container_width=True):
            st.session_state.orden_seleccionada = None
            st.rerun()

# --- PANTALLA 1: BIENVENIDA ---
if st.session_state.orden_seleccionada is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="welcome-card">
                <h1 class="brand-title" style="color: #D4AF37 !important; font-size: 38px; margin-bottom: 10px; font-weight: 800;">crealag</h1>
                <h2 style="color: #F8FAFC !important; font-weight: 700; margin-bottom: 20px; font-size: 24px;">Sistema de Supervisión</h2>
                <p style="color: #94A3B8 !important; font-size: 16px; font-weight: 600;">Seleccione la Orden de Compra que desea monitorear en tiempo real.</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if lista_ocs:
            with st.form("form_bienvenida"):
                oc_elegida = st.selectbox("Seleccione una Orden de Compra:", lista_ocs)
                st.markdown("<br>", unsafe_allow_html=True)
                btn_continuar = st.form_submit_button("Consultar Orden de Compra", use_container_width=True, type="primary")
            if btn_continuar:
                st.session_state.orden_seleccionada = oc_elegida
                st.rerun()
        else:
            st.warning("No hay Órdenes de Compra activas en el sistema.")

# --- PANTALLA 2: DATOS EN TIEMPO REAL ---
else:
    oc_actual = st.session_state.orden_seleccionada
    
    st.markdown(f"<h1 class='brand-title' style='font-size: 30px;'>crealag <span style='font-weight: 400; font-size: 24px; color: #94A3B8 !important;'>| Orden de Compra: <b>{oc_actual}</b></span></h1>", unsafe_allow_html=True)
    st.markdown("---")

    row_oc_info = df_ocs_catalogo[df_ocs_catalogo["orden_compra"] == oc_actual].iloc[0] if not df_ocs_catalogo.empty and oc_actual in df_ocs_catalogo["orden_compra"].values else {"meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}
    meta_oc = int(row_oc_info.get("meta_piezas", 1700))
    estado_oc = str(row_oc_info.get("estado", "Activa"))

    df_oc_prod = df_produccion[df_produccion["orden_compra"] == oc_actual] if not df_produccion.empty and "orden_compra" in df_produccion.columns else pd.DataFrame()
    total_producido = int(df_oc_prod["piezas_producidas"].sum()) if not df_oc_prod.empty else 0
    piezas_entregadas = int(row_oc_info.get("piezas_entregadas", 0) if pd.notnull(row_oc_info.get("piezas_entregadas")) else 0)
    piezas_almacen = max(0, total_producido - piezas_entregadas)

    if total_producido >= meta_oc:
        st.success(f"🟢 **ESTADO DE LA ORDEN:** ¡TERMINADA! Se alcanzó o superó la meta de {meta_oc} piezas.")
    else:
        st.warning(f"🟡 **ESTADO DE LA ORDEN:** EN PROCESO (Faltan {max(0, meta_oc - total_producido)} piezas para completar la meta estimada).")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Meta Estimada OC", f"{meta_oc} pzas")
    m2.metric("Producido Total", f"{total_producido} pzas")
    m3.metric("Entregadas / Remitidas", f"{piezas_entregadas} pzas")
    m4.metric("Disponibles en Almacén", f"{piezas_almacen} pzas")

    porcentaje = min(1.0, total_producido / meta_oc) if meta_oc > 0 else 0.0
    st.progress(porcentaje)

    st.markdown("---")

    # --- REGISTRO DIARIO CON ESTRUCTURA FIJA Y PAREJA ---
    st.markdown(f"### 📋 Detalle Consolidado de Producción por Día - `{oc_actual}`")

    if not df_oc_prod.empty:
        df_oc_prod['fecha_dt'] = pd.to_datetime(df_oc_prod['fecha'])
        df_resumen_diario = df_oc_prod.groupby('fecha_dt', as_index=False)['piezas_producidas'].sum().sort_values(by='fecha_dt', ascending=False)
        df_resumen_diario['Fecha'] = df_resumen_diario['fecha_dt'].dt.strftime('%d / %m / %Y')
        df_resumen_diario['Piezas Fabricadas'] = df_resumen_diario['piezas_producidas'].apply(lambda x: f"{x} pzas")

        # Tabla de ancho fijo estático
        st.dataframe(
            df_resumen_diario[['Fecha', 'Piezas Fabricadas']],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        csv_reporte_gen = df_resumen_diario[['Fecha', 'piezas_producidas']].rename(columns={'piezas_producidas': 'Piezas'}).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte Consolidado (CSV)",
            data=csv_reporte_gen,
            file_name=f"Reporte_Produccion_{oc_actual}.csv",
            mime="text/csv"
        )
    else:
        st.info("Aún no hay registros de producción para esta orden en la base de datos.")