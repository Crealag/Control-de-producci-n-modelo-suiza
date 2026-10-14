import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from supabase import create_client
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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

# Estilos CSS con paleta Crealag (Azul Noche y Bronce)
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

# Archivo de configuración local para el registro y catálogo de Órdenes de Compra
CONFIG_FILE = "oc_catalogo.csv"

def cargar_catalogo_ocs():
    import os
    if os.path.exists(CONFIG_FILE):
        df_cfg = pd.read_csv(CONFIG_FILE)
        if not df_cfg.empty:
            return df_cfg
    # Catálogo inicial por defecto
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

# --- BARRA LATERAL (Navegación y Administración de Órdenes de Compra) ---
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
    
    # Selector de la OC activa en todo el sistema
    lista_ocs = df_ocs_catalogo["Orden_Compra"].tolist()
    oc_actual = st.selectbox("Seleccionar OC Activa:", lista_ocs)
    
    # Obtener la meta de la OC seleccionada
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

# Título principal con branding integrado
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

    observaciones_turno = st.text_input("Observaciones del Turno:", placeholder="Ej. Ajuste en prensa...")

    if piezas_sumar > 0:
        exito = insertar_registro(oc_actual, fecha_registro, hora_registro, piezas_sumar, observaciones_turno if observaciones_turno else "Sin observaciones")
        if exito:
            st.success(f"✅ ¡Registradas {piezas_sumar} piezas en Supabase!")
            st.rerun()

    st.markdown("---")

    # --- HISTORIAL ---
    st.subheader(f"📋 Historial en Nube - {oc_actual}")
    if not df_oc.empty:
        st.dataframe(df_oc.sort_values(by="id", ascending=False), use_container_width=True)
        csv_reporte_gen = df_oc.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte Parcial",
            data=csv_reporte_gen,
            file_name=f"Reporte_Parcial_{oc_actual}.csv",
            mime="text/csv"
        )
    else:
        st.info("Aún no hay registros en esta Orden de Compra en la base de datos.")

    st.markdown("---")

    # --- GRÁFICAS ADAPTABLES (Por Día y Por Hora 8am-6pm excluyendo comida 1pm-2pm) ---
    st.subheader("📈 Gráficas de Rendimiento")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("##### 🕒 Ritmo por Hora (8:00 AM - 6:00 PM)")
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        df_hoy = df[df["fecha"] == hoy_str] if not df.empty and "fecha" in df.columns else pd.DataFrame()

        if not df_hoy.empty:
            df_h = df_hoy.copy()
            # Extraer la hora en formato entero para filtrar el horario laboral de 8 a 18 horas excluyendo las 13 hrs (comida)
            df_h['Hora_Int'] = pd.to_datetime(df_h['hora'], format='%H:%M:%S', errors='coerce').dt.hour
            # Filtrar de 8:00 a 18:00 excluyendo la hora 13 (1:00 PM a 2:00 PM)
            df_h = df_h[(df_h['Hora_Int'] >= 8) & (df_h['Hora_Int'] <= 18) & (df_h['Hora_Int'] != 13)]
            
            if not df_h.empty:
                df_h['Rango_Hora'] = df_h['Hora_Int'].apply(lambda x: f"{x:02d}:00 - {x+1:02d}:00")
                df_por_hora = df_h.groupby('Rango_Hora')['piezas_producidas'].sum()
                
                # Crear estructura completa de horas de la jornada para que la gráfica muestre los huecos si no hay producción
                horas_jornada = [f"{h:02d}:00 - {h+1:02d}:00" for h in [8,9,10,11,12,14,15,16,17]]
                df_por_hora = df_por_hora.reindex(horas_jornada, fill_value=0)
                st.bar_chart(df_por_hora)
            else:
                st.info("💡 Sin registros en horario laboral hoy (excluyendo hora de comida 1-2 PM).")
        else:
            st.info("💡 Sin registros para el día de hoy.")

    with col_g2:
        st.markdown(f"##### 📅 Producción Acumulada por Día (`{oc_actual}`)")
        if not df_oc.empty:
            df_dias = df_oc.copy()
            df_por_dia = df_dias.groupby('fecha')['piezas_producidas'].sum()
            st.line_chart(df_por_dia)
        else:
            st.info("💡 Sin registros diarios en esta OC.")

# --- SECCIÓN 2: GENERADOR DE REMISIONES (Con stock disponible en almacén) ---
elif menu_seleccionado == "📄 Generador de Remisiones":
    st.subheader("Generador de Remisiones Oficiales")
    
    # Cálculo automático de piezas disponibles en almacén para la OC activa
    df_oc_rem = df[df["orden_compra"] == oc_actual] if not df.empty and "orden_compra" in df.columns else pd.DataFrame()
    piezas_producidas_total = df_oc_rem["piezas_producidas"].sum() if not df_oc_rem.empty else 0
    
    st.info(f"📦 **Estado de Almacén para `{oc_actual}`:** Total Producido en Nube: **{piezas_producidas_total} piezas** (Meta total: {meta_actual}).")

    with st.form("form_remision"):
        col1, col2 = st.columns(2)
        with col1:
            atencion = st.text_input("Atención (Contacto)", "Ing. Laura Zamora")
            compania = st.text_input("Compañía", "Herwong")
            puesto = st.text_input("Puesto", "Compras")
            email = st.text_input("Email", "compras.herwong@gmail.com")
            cel = st.text_input("Cel", "871-1442234")
            
        with col2:
            referencia = st.text_input("Referencia", "Respaldos sillas modelo Suiza")
            documento = st.text_input("Documento (Folio)", f"{oc_actual}-REM")
            referencia_cliente = st.text_input("Referencia cliente", f"Pedido No. 01")
            fecha_remision = st.date_input("Fecha", datetime.now())
            
            # Cantidad a entregar en esta remisión (limitada al total producido disponible)
            cantidad_piezas = st.number_input("Cantidad de piezas a entregar en esta remisión", min_value=1, max_value=max(1, piezas_producidas_total), value=min(15, piezas_producidas_total if piezas_producidas_total > 0 else 1))

        fecha_recibido_str = st.text_input("Fecha en que se recibió el pedido (Texto)", "08 de mayo de 2026")

        submit_pdf = st.form_submit_button("Generar PDF de Remisión")

    if submit_pdf:
        def generar_pdf():
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            story = []
            
            styles = getSampleStyleSheet()
            style_normal = styles['Normal']
            
            style_titulo = ParagraphStyle('TituloCrealag', parent=style_normal, fontName='Helvetica-Bold', fontSize=24, textColor=colors.HexColor('#0A0F1D'))
            style_sub = ParagraphStyle('SubCrealag', parent=style_normal, fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#334155'))
            
            story.append(Paragraph("<b>crealag</b>", style_titulo))
            story.append(Paragraph("Fabricante mueblerio metalformado A.C. e INOX", style_sub))
            story.append(Spacer(1, 15))
            
            data_meta = [
                [Paragraph("<b>Atención:</b>", style_normal), Paragraph(atencion, style_normal), Paragraph("<b>Documento:</b>", style_normal), Paragraph(documento, style_normal)],
                [Paragraph("<b>Compañía:</b>", style_normal), Paragraph(compania, style_normal), Paragraph("<b>Referencia cliente:</b>", style_normal), Paragraph(referencia_cliente, style_normal)],
                [Paragraph("<b>Puesto:</b>", style_normal), Paragraph(puesto, style_normal), Paragraph("<b>Fecha:</b>", style_normal), Paragraph(fecha_remision.strftime('%d / %m / %Y'), style_normal)],
                [Paragraph("<b>Email:</b>", style_normal), Paragraph(email, style_normal), Paragraph("<b>Referencia:</b>", style_normal), Paragraph(referencia, style_normal)],
                [Paragraph("<b>Cel:</b>", style_normal), Paragraph(cel, style_normal), Paragraph("", style_normal), Paragraph("", style_normal)]
            ]
            
            t_meta = Table(data_meta, colWidths=[95, 195, 110, 140])
            t_meta.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t_meta)
            story.append(Spacer(1, 25))
            
            texto_oficial = f"Referente a su pedido {referencia_cliente} recibido el {fecha_recibido_str}. Se hace entrega de {cantidad_piezas} piezas de respaldo de silla modelo Suiza (Orden de Compra: {oc_actual})."
            style_cuerpo = ParagraphStyle('CuerpoRem', parent=style_normal, fontName='Helvetica', fontSize=11, leading=16, textColor=colors.HexColor('#0F172A'))
            story.append(Paragraph(texto_oficial, style_cuerpo))
            
            story.append(Spacer(1, 180))
            
            data_firmas = [
                [Paragraph("___________________________________", style_normal), Paragraph("___________________________________", style_normal)],
                [Paragraph("<b>ENTREGA</b>", style_normal), Paragraph("<b>NOMBRE Y FIRMA RECIBE</b>", style_normal)]
            ]
            t_firmas = Table(data_firmas, colWidths=[270, 270])
            t_firmas.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t_firmas)
            
            doc.build(story)
            buffer.seek(0)
            return buffer

        pdf_buffer = generar_pdf()
        
        st.success("¡Remisión generada con éxito!")
        st.download_button(
            label="📥 Descargar Remisión en PDF",
            data=pdf_buffer,
            file_name=f"{documento}.pdf",
            mime="application/pdf"
        )