import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO
import os
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
            if "Estado" not in df_cfg.columns:
                df_cfg["Estado"] = "Activa"
            return df_cfg
    return pd.DataFrame([{"Orden_Compra": "HER-080526", "Meta_Piezas": 100, "Estado": "Activa"}])

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

def actualizar_registro_supabase(record_id, piezas, observaciones):
    try:
        supabase.table("Producción").update({
            "piezas_producidas": int(piezas),
            "observaciones_turno": observaciones
        }).eq("id", record_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar el registro: {e}")
        return False

def eliminar_registro_supabase(record_id):
    try:
        supabase.table("Producción").delete().eq("id", record_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar el registro: {e}")
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
    
    # Encabezado de Órdenes de Compra con botón de 3 puntos (popover)
    col_oc_title, col_oc_btn = st.columns([4, 1])
    with col_oc_title:
        st.header("📦 Órdenes")
    with col_oc_btn:
        with st.popover("⋮"):
            st.markdown("### Opciones de OC")
            accion_oc = st.radio("Acción:", ["Editar Meta/Estado", "Eliminar OC Actual"], key="menu_3_puntos_oc")

    lista_ocs = df_ocs_catalogo["Orden_Compra"].tolist()
    oc_actual = st.selectbox("Seleccionar OC Activa:", lista_ocs)
    
    row_oc_info = df_ocs_catalogo[df_ocs_catalogo["Orden_Compra"] == oc_actual].iloc[0]
    meta_actual = int(row_oc_info["Meta_Piezas"])
    estado_oc = str(row_oc_info["Estado"]) if "Estado" in df_ocs_catalogo.columns else "Activa"
    
    if estado_oc == "Cerrada":
        st.error(f"🔒 OC `{oc_actual}` CERRADA (Solo lectura)")
    else:
        st.success(f"🟢 OC `{oc_actual}` Activa")

    # Acciones desplegadas desde el menú de 3 puntos
    if accion_oc == "Editar Meta/Estado":
        with st.expander("✏️ Configurar Orden Actual", expanded=True):
            meta_editada = st.number_input("Meta de piezas:", min_value=1, value=meta_actual, step=10, key="edit_meta_input")
            estado_editado = st.selectbox("Estado de la OC:", ["Activa", "Cerrada"], index=0 if estado_oc == "Activa" else 1, key="edit_estado_input")
            
            if st.button("Guardar Cambios OC"):
                df_ocs_catalogo.loc[df_ocs_catalogo["Orden_Compra"] == oc_actual, "Meta_Piezas"] = meta_editada
                df_ocs_catalogo.loc[df_ocs_catalogo["Orden_Compra"] == oc_actual, "Estado"] = estado_editado
                guardar_catalogo_ocs(df_ocs_catalogo)
                st.success(f"✅ OC `{oc_actual}` actualizada.")
                st.rerun()
    elif accion_oc == "Eliminar OC Actual":
        with st.expander("🗑️ Zona de Peligro", expanded=True):
            st.warning(f"¿Estás seguro de eliminar la OC `{oc_actual}` del catálogo?")
            if st.button("⚠️ Confirmar Eliminación de OC", type="primary"):
                if len(df_ocs_catalogo) > 1:
                    df_ocs_catalogo = df_ocs_catalogo[df_ocs_catalogo["Orden_Compra"] != oc_actual]
                    guardar_catalogo_ocs(df_ocs_catalogo)
                    st.success(f"🗑️ OC `{oc_actual}` eliminada.")
                    st.rerun()
                else:
                    st.error("No puedes eliminar la última Orden de Compra del sistema.")

    with st.expander("➕ Registrar Nueva Orden de Compra"):
        nueva_oc_input = st.text_input("Nueva OC (Ej. HER-101026)")
        nueva_meta_input = st.number_input("Meta de piezas:", min_value=1, value=100, step=10)
        
        if st.button("Guardar Nueva OC"):
            if nueva_oc_input and nueva_oc_input not in lista_ocs:
                nuevo_row = pd.DataFrame([{"Orden_Compra": nueva_oc_input, "Meta_Piezas": nueva_meta_input, "Estado": "Activa"}])
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

    st.subheader(f"Panel de Control - Orden Activa: `{oc_actual}` ({estado_oc})")

    m1, m2, m3 = st.columns(3)
    m1.metric("OC Activa", oc_actual)
    m2.metric("Producidas / Meta", f"{piezas_producidas_oc} / {meta_actual}")
    m3.metric("Avance", f"{int(porcentaje * 100)}%")

    st.progress(porcentaje)

    if piezas_producidas_oc >= meta_actual and meta_actual > 0:
        st.success(f"📌 **PRODUCCIÓN CUMPLIDA:** Se alcanzó la meta de **{piezas_producidas_oc}** piezas para la `{oc_actual}`.")

    st.markdown("---")

    if estado_oc == "Cerrada":
        st.warning(f"⚠️ La Orden de Compra **{oc_actual}** está cerrada. El panel se encuentra en modo de solo lectura.")
    else:
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

    # HISTORIAL
    st.subheader(f"📋 Historial en Nube - {oc_actual}")
    if not df_oc.empty:
        st.dataframe(df_oc.sort_values(by="id", ascending=False), use_container_width=True)
        
        # --- OPCIÓN DE EDICIÓN O ELIMINACIÓN DE REGISTROS INDIVIDUALES ---
        with st.expander("✏️ Editar o Eliminar un Registro de Producción"):
            ids_registros = df_oc["id"].tolist()
            id_seleccionado = st.selectbox("Selecciona el ID del registro a modificar:", ids_registros)
            
            row_sel = df_oc[df_oc["id"] == id_seleccionado].iloc[0]
            piezas_actuales = int(row_sel["piezas_producidas"])
            obs_actuales = str(row_sel["observaciones_turno"])
            
            col_edit1, col_edit2 = st.columns(2)
            with col_edit1:
                nuevas_piezas_input = st.number_input("Cantidad corregida:", min_value=0, value=piezas_actuales, step=1)
            with col_edit2:
                nuevas_obs_input = st.text_input("Observaciones corregidas:", value=obs_actuales)
                
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("💾 Guardar Cambios en Registro", type="primary"):
                    if actualizar_registro_supabase(id_seleccionado, nuevas_piezas_input, nuevas_obs_input):
                        st.success(f"✅ Registro ID `{id_seleccionado}` actualizado.")
                        st.rerun()
            with col_act2:
                if st.button("🗑️ Eliminar Registro"):
                    if eliminar_registro_supabase(id_seleccionado):
                        st.success(f"🗑️ Registro ID `{id_seleccionado}` eliminado.")
                        st.rerun()

        csv_reporte_gen = df_oc.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte Parcial (CSV)",
            data=csv_reporte_gen,
            file_name=f"Remision_Reporte_{oc_actual}.csv",
            mime="text/csv"
        )
    else:
        st.info("Aún no hay registros en esta Orden de Compra en la base de datos.")

    st.markdown("---")

    # GRÁFICAS
    st.subheader("📈 Gráficas de Rendimiento")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("##### 🕒 Ritmo por Hora (8:00 AM - 6:00 PM)")
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        df_hoy = df[df["fecha"] == hoy_str] if not df.empty and "fecha" in df.columns else pd.DataFrame()

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

# --- SECCIÓN 2: GENERADOR DE REMISIONES ---
elif menu_seleccionado == "📄 Generador de Remisiones":
    st.subheader("Generador de Remisiones Oficiales - Formato Original Crealag")
    
    df_oc_rem = df[df["orden_compra"] == oc_actual] if not df.empty and "orden_compra" in df.columns else pd.DataFrame()
    piezas_producidas_total = df_oc_rem["piezas_producidas"].sum() if not df_oc_rem.empty else 0
    
    st.info(f"📦 **Estado de Almacén para `{oc_actual}`:** Total Producido en Nube: **{piezas_producidas_total} piezas**.")

    with st.form("form_remision"):
        col1, col2 = st.columns(2)
        with col1:
            atencion = st.text_input("Atención", "Ing. Laura Zamora")
            compania = st.text_input("Compañía", "Herwong")
            puesto = st.text_input("Puesto", "Compras")
            email = st.text_input("Email", "compras.herwong@gmail.com")
            cel = st.text_input("Cel", "871-1442234")
            
        with col2:
            referencia = st.text_input("Referencia", "Respaldos sillas modelo Suiza")
            fecha_remision = st.date_input("Fecha de emisión", datetime.now())
            cantidad_piezas = st.number_input("Cantidad de piezas a entregar", min_value=1, value=max(1, int(piezas_producidas_total)))

        fecha_recibido_str = st.text_input("Fecha de pedido recibido (Texto)", "08 de mayo de 2026")

        submit_pdf = st.form_submit_button("Generar PDF de Remisión Original")

    if submit_pdf:
        def generar_pdf_original():
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=letter, 
                rightMargin=36, 
                leftMargin=36, 
                topMargin=36, 
                bottomMargin=15,
                title="Remision",
                author="Crealag"
            )
            story = []
            
            styles = getSampleStyleSheet()
            style_normal = styles['Normal']
            
            # 1. ENCABEZADO CON LOGO Y LÍNEA OSCURA SUPERIOR
            style_logo = ParagraphStyle('LogoCrealag', fontName='Helvetica-Bold', fontSize=28, textColor=colors.HexColor('#0A0F1D'), leading=30)
            story.append(Paragraph("<b>crealag</b>", style_logo))
            story.append(Spacer(1, 4))
            
            tabla_linea = Table([['']], colWidths=[540], rowHeights=[2.5])
            tabla_linea.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0A0F1D')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(tabla_linea)
            story.append(Spacer(1, 20))
            
            # 2. BLOQUE DE CAMPOS VERTICALES
            style_label = ParagraphStyle('LabelEstilo', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0F172A'))
            style_val = ParagraphStyle('ValEstilo', fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#0F172A'))
            
            data_campos = [
                [Paragraph("<b>Atención:</b>", style_label), Paragraph(atencion, style_val)],
                [Paragraph("<b>Compañía:</b>", style_label), Paragraph(compania, style_val)],
                [Paragraph("<b>Puesto:</b>", style_label), Paragraph(puesto, style_val)],
                [Paragraph("<b>Email:</b>", style_label), Paragraph(email, style_val)],
                [Paragraph("<b>Cel:</b>", style_label), Paragraph(cel, style_val)],
                [Paragraph("<b>Referencia:</b>", style_label), Paragraph(referencia, style_val)],
                [Paragraph("<b>Documento:</b>", style_label), Paragraph("FTO:2026-REM-1", style_val)],
                [Paragraph("<b>Referencia cliente:</b>", style_label), Paragraph(oc_actual, style_val)],
                [Paragraph("<b>Fecha:</b>", style_label), Paragraph(fecha_remision.strftime('%d / %m / %Y'), style_val)]
            ]
            
            t_campos = Table(data_campos, colWidths=[130, 380])
            t_campos.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('TOPPADDING', (0,0), (-1,-1), 3),
            ]))
            story.append(t_campos)
            story.append(Spacer(1, 25))
            
            # 3. TEXTO OFICIAL
            texto_cuerpo = f"Referente a su pedido {oc_actual} recibido el {fecha_recibido_str}. Se hace entrega de {cantidad_piezas} piezas de respaldo de silla modelo Suiza."
            style_cuerpo = ParagraphStyle('CuerpoRemision', fontName='Helvetica', fontSize=10.5, leading=16, textColor=colors.HexColor('#0F172A'))
            story.append(Paragraph(texto_cuerpo, style_cuerpo))
            
            # Espacio amplio para separar el texto de las firmas
            story.append(Spacer(1, 260))
            
            # 5. LÍNEAS DE FIRMA CON TEXTO CENTRADO
            style_firma_texto = ParagraphStyle('FirmaTexto', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#0F172A'), alignment=1)
            
            data_firmas = [
                [Paragraph("____________________________________________", style_normal), Paragraph("____________________________________________", style_normal)],
                [Paragraph("ENTREGA", style_firma_texto), Paragraph("NOMBRE Y FIRMA RECIBE", style_firma_texto)]
            ]
            t_firmas = Table(data_firmas, colWidths=[270, 270])
            t_firmas.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(t_firmas)
            
            # Espacio para empujar el pie de página exactamente al fondo de la hoja
            story.append(Spacer(1, 75))
            
            # 6. PIE DE PÁGINA OFICIAL
            story.append(tabla_linea)
            story.append(Spacer(1, 6))
            
            style_foot_val = ParagraphStyle('FootVal', fontName='Helvetica', fontSize=7.5, textColor=colors.HexColor('#0F172A'), leading=9)
            
            col_contacto = [
                Paragraph("<b>Contacto:</b> contacto@crealag.mx", style_foot_val),
                Paragraph("<b>Web:</b> crealag.com", style_foot_val),
                Paragraph("<b>Tel:</b> +52 871 185 5001", style_foot_val),
            ]
            
            col_direccion = [
                Paragraph("<b>Crealag SA de CV</b>", style_foot_val),
                Paragraph("Perif. Gomez Lerdo KM12 No. 0", style_foot_val),
                Paragraph("Periferico C.P.35150 CD Lerdo Durango", style_foot_val),
            ]
            
            col_folio = [
                Paragraph("", style_foot_val),
                Paragraph("", style_foot_val),
                Paragraph("FTO:2026-REM-1", style_foot_val),
            ]
            
            t_footer = Table([[col_contacto, col_direccion, col_folio]], colWidths=[180, 240, 100])
            t_footer.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (2,0), (2,-1), 'RIGHT'),
            ]))
            story.append(t_footer)
            
            doc.build(story)
            buffer.seek(0)
            return buffer

        pdf_buffer = generar_pdf_original()
        
        st.success("¡Remisión con formato original Crealag generada con éxito!")
        st.download_button(
            label="📥 Descargar Remisión en PDF",
            data=pdf_buffer,
            file_name="Remision.pdf",
            mime="application/pdf"
        )