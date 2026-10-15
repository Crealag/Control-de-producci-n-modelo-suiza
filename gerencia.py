import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from supabase import create_client

# Configuración de la página con la identidad corporativa de Crealag (Sistema de Supervisión)
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

# Estilos CSS - Paleta Clara / Fondo Blanco con Controles Sobrios y Elegantes
st.markdown("""
    <style>
    /* Fondo global blanco suave */
    .stApp, [data-testid="stHeader"], [data-testid="stToolbar"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    
    /* Barra lateral */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    
    /* Textos, títulos y párrafos */
    h1, h2, h3, h4, h5, h6, p, span, label, div, .stMarkdown {
        color: #0F172A !important;
    }
    
    /* Menús desplegables / Selects en tema claro sobrio */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    [data-baseweb="popover"], [data-baseweb="menu"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    
    /* Botones sobrios sin colores fosforescentes (gris oscuro corporativo) */
    .stButton>button, button[kind="primary"], div.stButton > button {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover, button[kind="primary"]:hover, div.stButton > button:hover {
        background-color: #0F172A !important;
        border-color: #0F172A !important;
        color: #FFFFFF !important;
    }

    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #475569 !important;
    }
    
    /* Marca Crealag */
    .brand-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        color: #0F172A !important;
    }
    
    /* Tarjeta de bienvenida */
    .welcome-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

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
    st.markdown("<h2 class='brand-title' style='color: #B45309 !important; margin-bottom: 0px;'>crealag</h2>", unsafe_allow_html=True)
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
                <h1 class="brand-title" style="color: #B45309 !important; font-size: 36px; margin-bottom: 10px;">crealag</h1>
                <h3 style="color: #0F172A !important; font-weight: 500; margin-bottom: 20px;">Sistema de Supervisión</h3>
                <p style="color: #64748B !important; font-size: 15px;">Seleccione la Orden de Compra que desea monitorear en tiempo real.</p>
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

# --- PANTALLA 2: DATOS EN TIEMPO REAL Y CALENDARIO ---
else:
    oc_actual = st.session_state.orden_seleccionada
    
    st.markdown(f"<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #64748B !important;'>| Orden de Compra: <b>{oc_actual}</b></span></h1>", unsafe_allow_html=True)
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

    # --- CALENDARIO VISUAL EN FONDO CLARO ---
    st.markdown(f"### 📅 Calendario de Producción - `{oc_actual}`")

    if not df_oc_prod.empty:
        df_oc_prod['fecha_dt'] = pd.to_datetime(df_oc_prod['fecha'])
        df_diario = df_oc_prod.groupby(df_oc_prod['fecha_dt'].dt.date)['piezas_producidas'].sum().to_dict()
        
        fechas_disponibles = sorted(list(df_diario.keys()))
        min_fecha = fechas_disponibles[0] if fechas_disponibles else date.today()
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            anio_sel = st.selectbox("Año:", sorted(list(set([f.year for f in fechas_disponibles]))), index=0)
        with col_sel2:
            meses_nombres = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 
                             7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
            mes_sel = st.selectbox("Mes:", options=list(meses_nombres.keys()), format_func=lambda x: meses_nombres[x], index=min_fecha.month - 1 if min_fecha.year == anio_sel else 0)

        cols_header = st.columns(7)
        dias_semana_nombres = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for idx, d_nombre in enumerate(dias_semana_nombres):
            cols_header[idx].markdown(f"**<div style='text-align: center; color: #475569 !important;'>{d_nombre}</div>**", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        cal = calendar.Calendar(firstweekday=0)
        dias_mes = cal.monthdayscalendar(anio_sel, mes_sel)

        for semana in dias_mes:
            cols_semana = st.columns(7)
            for idx, dia in enumerate(semana):
                with cols_semana[idx]:
                    if dia == 0:
                        st.write("")
                    else:
                        fecha_curr = date(anio_sel, mes_sel, dia)
                        pzas = df_diario.get(fecha_curr, 0)
                        
                        if pzas > 0:
                            st.markdown(f"""
                                <div style="background-color: #FEF3C7; border: 1px solid #F59E0B; border-radius: 8px; padding: 10px; text-align: center;">
                                    <div style="font-size: 16px; font-weight: bold; color: #78350F !important;">{dia}</div>
                                    <div style="background-color: #D4AF37; color: #0A0F1D !important; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 2px 4px; margin-top: 4px;">⚡ {pzas} pzas</div>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px; text-align: center;">
                                    <div style="font-size: 16px; font-weight: bold; color: #94A3B8 !important;">{dia}</div>
                                    <div style="font-size: 11px; color: #CBD5E1 !important; margin-top: 4px;">-</div>
                                </div>
                            """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.