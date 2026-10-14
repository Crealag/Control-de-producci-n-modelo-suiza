import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
from supabase import create_client

# Configuración de la página
st.set_page_config(
    page_title="Control - Modelo Suiza", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CREDENCIALES DE SUPABASE ---
SUPABASE_URL = "https://jdihosehcvvzsbhnqvf.supabase.co"
SUPABASE_KEY = "sb_publishable_D79R2pyWt6LI3lggygrbjg_4oJmoEX_"

@st.cache_resource
def init_supabase():
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client
    except Exception:
        return None

supabase = init_supabase()

# --- ESTILOS CSS PARA MÓVIL Y LAPTOP ---
st.markdown("""
    <style>
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5rem;
    }
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 0.8rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Archivos locales de configuración y respaldo
CONFIG_FILE = "oc_config.csv"
LOCAL_DB_FILE = "produccion_local.csv"

def cargar_config_oc():
    if os.path.exists(CONFIG_FILE):
        try:
            df_cfg = pd.read_csv(CONFIG_FILE)
            if not df_cfg.empty:
                return str(df_cfg.iloc[0]["Orden_Compra"]), int(df_cfg.iloc[0]["Meta_Piezas"])
        except Exception:
            pass
    return "HC-0505", 1700

def guardar_config_oc(oc, meta):
    df_cfg = pd.DataFrame([{"Orden_Compra": oc, "Meta_Piezas": meta}])
    df_cfg.to_csv(CONFIG_FILE, index=False)

oc_actual, meta_actual = cargar_config_oc()

# --- FUNCIONES DE DATOS (Híbridas: Nube + Respaldo Local) ---
def cargar_datos():
    columnas = ["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"]
    
    if supabase is not None:
        try:
            response = supabase.table("produccion").select("*").execute()
            data = response.data
            if data:
                df_cloud = pd.DataFrame(data)
                df_cloud.to_csv(LOCAL_DB_FILE, index=False)
                return df_cloud
        except Exception:
            pass

    if os.path.exists(LOCAL_DB_FILE):
        try:
            df_local = pd.read_csv(LOCAL_DB_FILE)
            if not df_local.empty:
                return df_local
        except Exception:
            pass
            
    return pd.DataFrame(columns=columnas)

def insertar_registro(orden, fecha, hora, piezas, observaciones):
    nuevo_registro = {
        "orden_compra": orden,
        "fecha": fecha,
        "hora": hora,
        "piezas_producidas": int(piezas),
        "observaciones_turno": observaciones
    }
    
    if supabase is not None:
        try:
            supabase.table("produccion").insert(nuevo_registro).execute()
        except Exception:
            pass

    try:
        df_actual = cargar_datos()
        nuevo_registro["id"] = len(df_actual) + 1
        df_nuevo = pd.concat([df_actual, pd.DataFrame([nuevo_registro])], ignore_index=True)
        df_nuevo.to_csv(LOCAL_DB_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar localmente: {e}")
        return False

df = cargar_datos()

# --- BARRA LATERAL (Configuración) ---
with st.sidebar:
    st.header("🏢 Configuración")
    
    if os.path.exists("logo.png"):
        st.image("logo.png", width="stretch")
    else:
        uploaded_logo = st.file_uploader("Sube el logo:", type=["png", "jpg", "jpeg"])
        if uploaded_logo is not None:
            st.image(uploaded_logo, width="stretch")

    st.markdown("---")
    st.header("📦 Orden de Compra")
    
    nueva_oc = st.text_input("Número de OC:", value=oc_actual)
    nueva_meta = st.number_input("Meta de piezas:", min_value=1, value=int(meta_actual), step=10)
    
    if st.button("Actualizar OC", type="primary"):
        guardar_config_oc(nueva_oc, nueva_meta)
        st.success("✅ Actualizado.")
        st.rerun()

# --- CÁLCULO DE PROGRESO ---
df_oc = df[df["orden_compra"] == oc_actual] if not df.empty and "orden_compra" in df.columns else pd.DataFrame()
piezas_producidas_oc = df_oc["piezas_producidas"].sum() if not df_oc.empty else 0
porcentaje = min(1.0, piezas_producidas_oc / meta_actual) if meta_actual > 0 else 0.0

# --- TÍTULO Y MÉTRICAS ---
st.title("🏭 Producción - Modelo Suiza")
st.caption(f"Orden Activa: **{oc_actual}** | Modo: {'☁️ Nube / 💾 Local'}")

m1, m2, m3 = st.columns(3)
m1.metric("OC", oc_actual)
m2.metric("Producidas", f"{piezas_producidas_oc} / {meta_actual}")
m3.metric("Avance", f"{int(porcentaje * 100)}%")

st.progress(porcentaje)

if piezas_producidas_oc >= meta_actual and meta_actual > 0:
    st.success(f"📌 **PRODUCCIÓN CUMPLIDA:** Se alcanzó la meta de **{piezas_producidas_oc}** piezas para la `{oc_actual}`.")
    
    csv_reporte = df_oc.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte Final (CSV)",
        data=csv_reporte,
        file_name=f"Reporte_Produccion_{oc_actual}.csv",
        mime="text/csv",
        type="primary"
    )

st.markdown("---")

# --- SECCIÓN DE CAPTURA ---
st.subheader("➕ Registrar Piezas")

tipo_captura = st.radio("Modo de registro:", ["Rápido / Actual", "Pasado (Fecha/Hora)"], horizontal=True)

piezas_sumar = 0
fecha_registro = datetime.now().strftime("%Y-%m-%d")
hora_registro = datetime.now().strftime("%H:%M:%S")

if tipo_captura == "Rápido / Actual":
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**Botones rápidos**")
        b1, b2, b3 = st.columns(3)
        if b1.button("+10"): piezas_sumar = 10
        if b2.button("+50"): piezas_sumar = 50
        if b3.button("+100"): piezas_sumar = 100

    with col2:
        st.markdown("**Ingreso manual**")
        cantidad_manual = st.number_input("Cantidad:", min_value=0, value=0, step=1, key="manual_actual")
        if st.button("Guardar", type="primary"):
            if cantidad_manual > 0:
                piezas_sumar = cantidad_manual
            else:
                st.warning("Ingresa un valor mayor a 0.")
else:
    st.markdown("**Registro con Fecha y Hora Personalizada**")
    f_pasada = st.date_input("Fecha:", value=date.today())
    h_pasada = st.time_input("Hora:", value=datetime.now().time())
    cantidad_pasada = st.number_input("Cantidad de piezas:", min_value=1, value=10, step=1, key="manual_pasada")
    
    fecha_registro = f_pasada.strftime("%Y-%m-%d")
    hora_registro = h_pasada.strftime("%H:%M:%S")
    
    if st.button("Guardar Registro Pasado", type="primary"):
        piezas_sumar = cantidad_pasada

observaciones = st.text_input("Observaciones (opcional):", placeholder="Ej. Ajuste en prensa...")

if piezas_sumar > 0:
    exito = insertar_registro(oc_actual, fecha_registro, hora_registro, piezas_sumar, observaciones if observaciones else "Sin observaciones")
    if exito:
        st.success(f"✅ ¡Registradas {piezas_sumar} piezas correctamente!")
        st.rerun()

st.markdown("---")

# --- HISTORIAL ---
st.subheader(f"📋 Historial - {oc_actual}")

if not df_oc.empty:
    st.dataframe(df_oc.sort_values(by="id", ascending=False), width="stretch")
    
    csv_reporte_gen = df_oc.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte Parcial",
        data=csv_reporte_gen,
        file_name=f"Reporte_Parcial_{oc_actual}.csv",
        mime="text/csv"
    )
else:
    st.info("Aún no hay registros en esta Orden de Compra.")

st.markdown("---")

# --- GRÁFICAS ADAPTABLES ---
st.subheader("📈 Gráficas de Rendimiento")

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("##### 🕒 Ritmo Diario (Por Hora)")
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    df_hoy = df[df["fecha"] == hoy_str] if not df.empty and "fecha" in df.columns else pd.DataFrame()

    if not df_hoy.empty:
        df_hoy_copia = df_hoy.copy()
        df_hoy_copia['Hora_Corta'] = pd.to_datetime(df_hoy_copia['hora'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:00')
        df_por_hora = df_hoy_copia.groupby('Hora_Corta')['piezas_producidas'].sum()
        st.line_chart(df_por_hora)
    else:
        st.info("💡 Sin registros hoy.")

with col_g2:
    st.markdown(f"##### 📦 Tendencia OC: `{oc_actual}`")
    if not df_oc.empty:
        df_grafica_oc = df_oc.copy()
        df_grafica_oc['Timestamp'] = pd.to_datetime(df_grafica_oc['fecha'] + ' ' + df_grafica_oc['hora'])
        df_grafica_oc = df_grafica_oc.sort_values('Timestamp')
        st.line_chart(df_grafica_oc.set_index('Timestamp')['piezas_producidas'])
    else:
        st.info("💡 Sin registros en la OC.")