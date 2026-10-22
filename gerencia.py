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
        return None

supabase = init_supabase()

# --- ESTILOS CSS EJECUTIVOS ---
css_estilos = """
<style>
.stApp { background-color: #080C14; color: #F8FAFC; font-family: 'Inter', sans-serif; }
div[data-baseweb="select"] { background-color: #111827 !important; color: #F8FAFC !important; border-color: #1F2937 !important; border-radius: 8px; }
.brand-title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px; }
[data-testid="stMetricValue"] { color: #F8FAFC !important; font-weight: 800 !important; font-size: 1.8rem !important; }
[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-weight: 600 !important; font-size: 0.85rem !important; text-transform: uppercase; letter-spacing: 0.5px; }

.exec-card {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #1E293B;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    margin-bottom: 20px;
}
.welcome-banner {
    background: linear-gradient(135deg, #111827 0%, #0F172A 100%);
    padding: 30px;
    border-radius: 12px;
    border-left: 5px solid #38BDF8;
    border-top: 1px solid #1F2937;
    border-right: 1px solid #1F2937;
    border-bottom: 1px solid #1F2937;
    margin-bottom: 25px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
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
        return pd.DataFrame([{"orden_compra": "HC-0505", "meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}])
    try:
        res = supabase.table("Órdenes_Compra").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame([{"orden_compra": "HC-0505", "meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}])

# --- ENCABEZADO ---
st.markdown("<h1 class='brand-title' style='font-size: 2rem;'>crealag <span style='font-weight: 300; font-size: 20px; color: #94A3B8;'>| Portal Gerencial Ejecutivo</span></h1>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #1E293B; margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# --- BANNER DE BIENVENIDA ---
st.markdown("""
<div class="welcome-banner">
    <h2 style="color: #F8FAFC; margin: 0 0 8px 0; font-size: 1.5rem;">¡Bienvenido al Portal Gerencial de Crealag!</h2>
    <p style="color: #94A3B8; margin: 0; font-size: 0.95rem; line-height: 1.5;">Espacio exclusivo para la supervisión y control ejecutivo de la producción, estatus de inventario en almacén y bitácoras operativas de piso.</p>
</div>
""", unsafe_allow_html=True)

df = cargar_datos_supabase()
df_ocs_catalogo = cargar_catalogo_ocs()

lista_ocs = df_ocs_catalogo["orden_compra"].tolist() if not df_ocs_catalogo.empty else ["HC-0505"]

# --- SELECTOR PRINCIPAL ---
opciones_selector = ["-- Selecciona una Orden de Compra --"] + lista_ocs
seleccion = st.selectbox("Selecciona la orden de compra a consultar", opciones_selector)

# Si no ha seleccionado ninguna orden, detenemos la ejecución de la página aquí mismo
if seleccion == "-- Selecciona una Orden de Compra --":
    st.stop()

# --- DESGLOSE DE INFORMACIÓN AL SELECCIONAR ---
oc_actual = seleccion

try:
    row_oc_info = df_ocs_catalogo[df_ocs_catalogo["orden_compra"] == oc_actual].iloc[0]
    meta_actual = int(row_oc_info.get("meta_piezas", 1700))
    estado_oc = str(row_oc_info.get("estado", "Activa"))
    entregadas_actual = int(row_oc_info.get("piezas_entregadas", 0) if pd.notnull(row_oc_info.get("piezas_entregadas")) else 0)
except Exception:
    meta_actual = 1700
    estado_oc = "Activa"
    entregadas_actual = 0

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

if not df.empty and "orden_compra" in df.columns:
    df_oc = df[df["orden_compra"] == oc_actual].copy()
    
    total_piezas_oc = df_oc["piezas_producidas"].sum() if not df_oc.empty else 0
    piezas_almacen_actual = max(0, total_piezas_oc - entregadas_actual)
    porcentaje = min(1.0, total_piezas_oc / meta_actual) if meta_actual > 0 else 0.0
    
    # --- TARJETA CONTENEDORA DE MÉTRICAS ---
    st.markdown(f"""
    <div class="exec-card">
        <div style="font-size: 1.1rem; font-weight: 700; color: #38BDF8; margin-bottom: 15px;">
            📊 Estatus General — Orden de Compra: {oc_actual} <span style="font-size: 0.8rem; background-color: #0369A1; color: #E0F2FE; padding: 3px 8px; border-radius: 4px; float: right;">{estado_oc}</span>
        </div>
    """, unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Meta Estimada OC", f"{meta_actual:,} pzas")
    m2.metric("Producido Total", f"{total_piezas_oc:,} pzas")
    m3.metric("Entregadas / Remitidas", f"{entregadas_actual:,} pzas")
    m4.metric("Disponibles en Almacén", f"{piezas_almacen_actual:,} pzas")
    
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    st.progress(porcentaje)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not df_oc.empty:
        df_oc['fecha_dt'] = pd.to_datetime(df_oc['fecha'])
        
        # Calcular rangos de semana
        df_oc['inicio_semana'] = df_oc['fecha_dt'] - pd.to_timedelta(df_oc['fecha_dt'].dt.dayofweek, unit='d')
        df_oc['fin_semana'] = df_oc['inicio_semana'] + pd.to_timedelta(6, unit='d')
        
        df_oc['semana_label'] = (
            "Del " + df_oc['inicio_semana'].dt.strftime('%d/%m/%Y') + 
            " al " + df_oc['fin_semana'].dt.strftime('%d/%m/%Y')
        )
        
        df_semanas_ordenadas = df_oc[['semana_label', 'inicio_semana']].drop_duplicates().sort_values('inicio_semana')
        semanas_disponibles = df_semanas_ordenadas['semana_label'].tolist()
        
        hoy = pd.Timestamp(date.today())
        inicio_hoy = hoy - pd.to_timedelta(hoy.dayofweek, unit='d')
        fin_hoy = inicio_hoy + pd.to_timedelta(6, unit='d')
        etiqueta_actual = f"Del {inicio_hoy.strftime('%d/%m/%Y')} al {fin_hoy.strftime('%d/%m/%Y')}"
        
        key_idx = f"semana_idx_{oc_actual}"
        
        if key_idx not in st.session_state:
            if etiqueta_actual in semanas_disponibles:
                st.session_state[key_idx] = semanas_disponibles.index(etiqueta_actual)
            else:
                st.session_state[key_idx] = len(semanas_disponibles) - 1

        if st.session_state[key_idx] >= len(semanas_disponibles):
            st.session_state[key_idx] = len(semanas_disponibles) - 1
        if st.session_state[key_idx] < 0:
            st.session_state[key_idx] = 0

        # --- CARRUSEL DE SEMANAS ---
        st.markdown("<h4 style='color: #F8FAFC; font-weight: 600; font-size: 1.1rem;'>📅 Periodo de Análisis Semanal</h4>", unsafe_allow_html=True)
        
        c_btn1, c_lbl, c_btn2 = st.columns([1, 4, 1])
        
        with c_btn1:
            if st.button("◀ Anterior", key=f"ant_{oc_actual}", use_container_width=True):
                if st.session_state[key_idx] > 0:
                    st.session_state[key_idx] -= 1
                    st.rerun()
                    
        with c_lbl:
            semana_seleccionada = semanas_disponibles[st.session_state[key_idx]]
            st.markdown(f"""
            <div style="background-color: #111827; padding: 11px; border-radius: 8px; text-align: center; border: 1px solid #1F2937; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                <span style="color: #38BDF8; font-weight: 700; font-size: 15px;">{semana_seleccionada}</span>
            </div>
            """, unsafe_allow_html=True)
            
        with c_btn2:
            if st.button("Siguiente ▶", key=f"sig_{oc_actual}", use_container_width=True):
                if st.session_state[key_idx] < len(semanas_disponibles) - 1:
                    st.session_state[key_idx] += 1
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='color: #F8FAFC; font-weight: 600; font-size: 1.1rem;'>📋 Bitácora y Novedades del Periodo</h4>", unsafe_allow_html=True)
        
        df_semana = df_oc[df_oc['semana_label'] == semana_seleccionada]
        fechas_semana = sorted(df_semana["fecha"].astype(str).unique(), reverse=True)
        
        if fechas_semana:
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
                    notas_resumidas = "Operación normal (Sin incidencias reportadas)"
                
                st.markdown(f"""
                <div style="background-color: #0F172A; padding: 16px; border-radius: 8px; border-left: 4px solid #38BDF8; border-top: 1px solid #1E293B; border-right: 1px solid #1E293B; border-bottom: 1px solid #1E293B; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
                    <div style="font-size: 15px; font-weight: bold; color: #F8FAFC; margin-bottom: 4px;">📅 Fecha: {f}</div>
                    <div style="color: #94A3B8; font-size: 13.5px; margin-bottom: 6px;">📦 Producción total del día: <b style="color: #F8FAFC;">{piezas_dia:,} pzas</b></div>
                    <div style="color: #E2E8F0; font-size: 13.5px;">📝 <b>Motivo / Novedades:</b> {notas_resumidas}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay registros en esta semana.")
    else:
        st.success("🎉 No hay registros de producción para esta orden.")
else:
    st.info("Aún no hay registros en la base de datos.")