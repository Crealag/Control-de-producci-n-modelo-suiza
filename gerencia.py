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

# Estilos CSS con paleta Crealag y diseño de Calendario Visual
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
    /* Estilos para el Calendario Visual */
    .calendar-container {
        background-color: #111B2E;
        border: 1px solid #2D3E5E;
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
    }
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 8px;
        text-align: center;
    }
    .calendar-header-day {
        font-weight: bold;
        color: #94A3B8;
        padding: 8px 0;
        font-size: 13px;
    }
    .calendar-day {
        background-color: #1A263D;
        border-radius: 8px;
        min-height: 75px;
        padding: 8px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border: 1px solid #2D3E5E;
    }
    .calendar-day-active {
        background-color: rgba(212, 175, 55, 0.15);
        border: 1px solid #D4AF37;
    }
    .day-number {
        font-size: 14px;
        font-weight: bold;
        color: #F8FAFC;
    }
    .day-badge {
        background-color: #D4AF37;
        color: #0A0F1D;
        font-size: 11px;
        font-weight: bold;
        padding: 2px 4px;
        border-radius: 4px;
        margin-top: 4px;
    }
    .day-empty {
        background-color: transparent;
        border: none;
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
    st.markdown("<h2 class='brand-title' style='color: #D4AF37; margin-bottom: 0px;'>crealag</h2>", unsafe_allow_html=True)
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
                <h1 class="brand-title" style="color: #D4AF37; font-size: 36px; margin-bottom: 10px;">crealag</h1>
                <h3 style="color: #F8FAFC; font-weight: 400; margin-bottom: 20px;">Sistema de Supervisión</h3>
                <p style="color: #94A3B8; font-size: 15px;">Seleccione la Orden de Compra que desea monitorear en tiempo real.</p>
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

# --- PANTALLA 2: DATOS EN TIEMPO REAL CON CALENDARIO VISUAL ---
else:
    oc_actual = st.session_state.orden_seleccionada
    
    st.markdown(f"<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Orden de Compra: <b>{oc_actual}</b></span></h1>", unsafe_allow_html=True)
    st.markdown("---")

    row_oc_info = df_ocs_catalogo[df_ocs_catalogo["orden_compra"] == oc_actual].iloc[0] if not df_ocs_catalogo.empty and oc_actual in df_ocs_catalogo["orden_compra"].values else {"meta_piezas": 100, "estado": "Activa", "piezas_entregadas": 0}
    meta_oc = int(row_oc_info.get("meta_piezas", 100))
    estado_oc = str(row_oc_info.get("estado", "Activa"))

    df_oc_prod = df_produccion[df_produccion["orden_compra"] == oc_actual] if not df_produccion.empty and "orden_compra" in df_produccion.columns else pd.DataFrame()
    total_producido = int(df_oc_prod["piezas_producidas"].sum()) if not df_oc_prod.empty else 0
    piezas_entregadas = int(row_oc_info.get("piezas_entregadas", 0))
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

    # --- CALENDARIO VISUAL INTERACTIVO ---
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

        cal = calendar.Calendar(firstweekday=0)
        dias_mes = cal.monthdayscalendar(anio_sel, mes_sel)
        
        nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        
        html_grid = "<div class='calendar-container'><div class='calendar-grid'>"
        for d in nombres_dias:
            html_grid += f"<div class='calendar-header-day'>{d}</div>"
            
        for semana in dias_mes:
            for dia in semana:
                if dia == 0:
                    html_grid += "<div class='calendar-day day-empty'></div>"
                else:
                    fecha_actual_obj = date(anio_sel, mes_sel, dia)
                    piezas_dia = df_diario.get(fecha_actual_obj, 0)
                    
                    if piezas_dia > 0:
                        html_grid += f"""
                        <div class='calendar-day calendar-day-active' title='{fecha_actual_obj}: {piezas_dia} piezas'>
                            <span class='day-number'>{dia}</span>
                            <span class='day-badge'>⚡ {piezas_dia} pzas</span>
                        </div>
                        """
                    else:
                        html_grid += f"""
                        <div class='calendar-day'>
                            <span class='day-number'>{dia}</span>
                        </div>
                        """
        html_grid += "</div></div>"
        
        st.markdown(html_grid, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("#### 🔍 Detalle por Fecha")
        fecha_elegida_detalle = st.date_input("Selecciona una fecha para ver piezas registradas:", value=min_fecha)
        
        df_detalle_dia = df_oc_prod[df_oc_prod['fecha_dt'].dt.date == fecha_elegida_detalle]
        if not df_detalle_dia.empty:
            total_dia_sel = df_detalle_dia['piezas_producidas'].sum()
            st.success(f"📌 Total fabricado el **{fecha_elegida_detalle.strftime('%d/%m/%Y')}**: **{total_dia_sel} piezas**")
        else:
            st.info(f"No hay registros de producción en la fecha {fecha_elegida_detalle.strftime('%d/%m/%Y')}.")

        st.markdown("---")
        csv_reporte_gen = df_oc_prod.groupby('fecha', as_index=False)['piezas_producidas'].sum().to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte Consolidado (CSV)",
            data=csv_reporte_gen,
            file_name=f"Reporte_Calendario_{oc_actual}.csv",
            mime="text/csv"
        )
    else:
        st.info("Aún no hay registros de producción para esta orden en la base de datos.")