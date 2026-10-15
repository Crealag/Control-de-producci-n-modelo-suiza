import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from supabase import create_client
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración de la página
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

# Estilos CSS
st.markdown("""
    <style>
    .stApp { background-color: #0A0F1D; color: #F8FAFC; }
    [data-testid="stSidebar"] { background-color: #111B2E; }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
        background-color: #1A263D !important; color: #F8FAFC !important; border-color: #2D3E5E !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #F8FAFC; border: 1px solid #D4AF37; border-radius: 6px; font-weight: 600;
    }
    .brand-title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800; color: #F8FAFC; }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE BASE DE DATOS (CATÁLOGO Y PRODUCCIÓN) ---
def cargar_catalogo_ocs():
    try:
        res = supabase.table("Órdenes_Compra").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame([{"orden_compra": "HC-0505", "meta_piezas": 100, "estado": "Activa", "piezas_entregadas": 0}])

def guardar_nueva_oc(orden, meta):
    supabase.table("Órdenes_Compra").insert({"orden_compra": orden, "meta_piezas": int(meta), "estado": "Activa"}).execute()

def actualizar_oc_supabase(orden, meta, estado):
    supabase.table("Órdenes_Compra").update({"meta_piezas": int(meta), "estado": estado}).eq("orden_compra", orden).execute()

def eliminar_oc_supabase(orden):
    supabase.table("Órdenes_Compra").delete().eq("orden_compra", orden).execute()
    supabase.table("Producción").delete().eq("orden_compra", orden).execute()

def cargar_datos_supabase():
    try:
        res = supabase.table("Producción").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])
    except Exception:
        return pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])

def insertar_registro(orden, fecha, hora, piezas, observaciones):
    supabase.table("Producción").insert({
        "orden_compra": orden, "fecha": fecha, "hora": hora,
        "piezas_producidas": int(piezas), "observaciones_turno": observaciones
    }).execute()

def actualizar_registro_supabase(record_id, piezas, observaciones):
    supabase.table("Producción").update({"piezas_producidas": int(piezas), "observaciones_turno": observaciones}).eq("id", record_id).execute()

def eliminar_registro_supabase(record_id):
    supabase.table("Producción").delete().eq("id", record_id).execute()

df_ocs_catalogo = cargar_catalogo_ocs()
df = cargar_datos_supabase()

# --- FUNCIÓN GENERADORA DE PDF ---
def generar_pdf_original(atencion, compania, puesto, email, cel, referencia, oc_actual, fecha_remision, cantidad_piezas, fecha_recibido_str):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=15,
        title="Remision", author="Crealag"
    )
    story = []
    styles = getSampleStyleSheet()
    style_normal = styles['Normal']
    
    style_logo = ParagraphStyle('LogoCrealag', fontName='Helvetica-Bold', fontSize=28, textColor=colors.HexColor('#0A0F1D'), leading=30)
    story.append(Paragraph("<b>crealag</b>", style_logo))
    story.append(Spacer(1, 4))
    
    tabla_linea = Table([['']], colWidths=[540], rowHeights=[2.5])
    tabla_linea.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0A0F1D'))]))
    story.append(tabla_linea)
    story.append(Spacer(1, 20))
    
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
    t_campos.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 3), ('TOPPADDING', (0,0), (-1,-1), 3)]))
    story.append(t_campos)
    story.append(Spacer(1, 25))
    
    texto_cuerpo = f"Referente a su pedido <b><u>{oc_actual}</u></b> recibido el <b><u>{fecha_recibido_str}</u></b>. Se hace entrega de <b><u>{cantidad_piezas}</u></b> piezas de respaldo de silla modelo Suiza."
    style_cuerpo = ParagraphStyle('CuerpoRemision', fontName='Helvetica', fontSize=10.5, leading=16, textColor=colors.HexColor('#0F172A'))
    story.append(Paragraph(texto_cuerpo, style_cuerpo))
    story.append(Spacer(1, 260))
    
    style_firma_texto = ParagraphStyle('FirmaTexto', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#0F172A'), alignment=1)
    data_firmas = [
        [Paragraph("____________________________________________", style_normal), Paragraph("____________________________________________", style_normal)],
        [Paragraph("ENTREGA", style_firma_texto), Paragraph("NOMBRE Y FIRMA RECIBE", style_firma_texto)]
    ]
    t_firmas = Table(data_firmas, colWidths=[270, 270])
    t_firmas.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_firmas)
    story.append(Spacer(1, 75))
    
    story.append(tabla_linea)
    story.append(Spacer(1, 6))
    style_foot_val = ParagraphStyle('FootVal', fontName='Helvetica', fontSize=7.5, textColor=colors.HexColor('#0F172A'), leading=9)
    col_contacto = [Paragraph("<b>Contacto:</b> contacto@crealag.mx", style_foot_val), Paragraph("<b>Web:</b> crealag.com", style_foot_val), Paragraph("<b>Tel:</b> +52 871 185 5001", style_foot_val)]
    col_direccion = [Paragraph("<b>Crealag SA de CV</b>", style_foot_val), Paragraph("Perif. Gomez Lerdo KM12 No. 0", style_foot_val), Paragraph("Periferico C.P.35150 CD Lerdo Durango", style_foot_val)]
    col_folio = [Paragraph("", style_foot_val), Paragraph("", style_foot_val), Paragraph("FTO:2026-REM-1", style_foot_val)]
    t_footer = Table([[col_contacto, col_direccion, col_folio]], colWidths=[180, 240, 100])
    t_footer.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (2,0), (2,-1), 'RIGHT')]))
    story.append(t_footer)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 class='brand-title' style='color: #D4AF37;'>crealag</h2>", unsafe_allow_html=True)
    st.caption("Fabricante mueblerio metalformado A.C. e INOX")
    st.markdown("---")
    
    menu_seleccionado = st.selectbox("Navegación del Sistema", ["📊 Producción y Registro", "📄 Generador de Remisiones"])
    st.markdown("---")
    
    col_oc_title, col_oc_btn = st.columns([4, 1])
    with col_oc_title:
        st.header("📦 Órdenes")
    with col_oc_btn:
        with st.popover("⋮"):
            st.markdown("### Opciones de OC")
            accion_oc = st.radio("Acción:", ["Editar Meta/Estado", "Eliminar OC Actual"], key="menu_3_puntos_oc")

    lista_ocs = df_ocs_catalogo["orden_compra"].tolist()
    oc_actual = st.selectbox("Seleccionar OC Activa:", lista_ocs)
    
    row_oc_info = df_ocs_catalogo[df_ocs_catalogo["orden_compra"] == oc_actual].iloc[0]
    meta_actual = int(row_oc_info["meta_piezas"])
    estado_oc = str(row_oc_info["estado"])
    
    if estado_oc == "Cerrada":
        st.error(f"🔒 OC `{oc_actual}` CERRADA (Solo lectura)")
    else:
        st.success(f"🟢 OC `{oc_actual}` Activa")

    if accion_oc == "Editar Meta/Estado":
        with st.expander("✏️ Configurar Orden Actual", expanded=True):
            meta_editada = st.number_input("Meta de piezas:", min_value=1, value=meta_actual, step=10, key="edit_meta_input")
            estado_editado = st.selectbox("Estado de la OC:", ["Activa", "Cerrada"], index=0 if estado_oc == "Activa" else 1, key="edit_estado_input")
            if st.button("Guardar Cambios OC"):
                actualizar_oc_supabase(oc_actual, meta_editada, estado_editado)
                st.success(f"✅ OC `{oc_actual}` actualizada en la nube.")
                st.rerun()
    elif accion_oc == "Eliminar OC Actual":
        with st.expander("🗑️ Zona de Peligro", expanded=True):
            st.warning(f"¿Eliminar `{oc_actual}` y todos sus registros?")
            if st.button("⚠️ Confirmar Eliminación", type="primary"):
                if len(df_ocs_catalogo) > 1:
                    eliminar_oc_supabase(oc_actual)
                    st.success(f"🗑️ OC `{oc_actual}` eliminada por completo.")
                    st.rerun()
                else:
                    st.error("No puedes eliminar la última Orden de Compra.")

    with st.expander("➕ Registrar Nueva Orden de Compra"):
        nueva_oc_input = st.text_input("Nueva OC (Ej. HER-101026)")
        nueva_meta_input = st.number_input("Meta de piezas:", min_value=1, value=100, step=10)
        if st.button("Guardar Nueva OC"):
            if nueva_oc_input and nueva_oc_input not in lista_ocs:
                guardar_nueva_oc(nueva_oc_input, nueva_meta_input)
                st.success(f"✅ OC `{nueva_oc_input}` creada en la nube.")
                st.rerun()

# --- VISTA PRINCIPAL ---
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Control de Producción y Remisiones</span></h1>", unsafe_allow_html=True)
st.markdown("---")

if menu_seleccionado == "📊 Producción y Registro":
    df_oc = df[df["orden_compra"] == oc_actual] if not df.empty else pd.DataFrame()
    piezas_producidas_oc = df_oc["piezas_producidas"].sum() if not df_oc.empty else 0
    porcentaje = min(1.0, piezas_producidas_oc / meta_actual) if meta_actual > 0 else 0.0

    st.subheader(f"Panel de Control - Orden Activa: `{oc_actual}` ({estado_oc})")
    m1, m2, m3 = st.columns(3)
    m1.metric("OC Activa", oc_actual)
    m2.metric("Producidas / Meta", f"{piezas_producidas_oc} / {meta_actual}")
    m3.metric("Avance", f"{int(porcentaje * 100)}%")
    st.progress(porcentaje)

    st.markdown("---")

    if estado_oc != "Cerrada":
        st.subheader("➕ Registrar Piezas")
        tipo_captura = st.radio("Modo de registro:", ["Rápido / Actual", "Pasado (Fecha/Hora)"], horizontal=True)
        piezas_sumar = 0
        fecha_registro = datetime.now().strftime("%Y-%m-%d")
        hora_registro = datetime.now().strftime("%H:%M:%S")

        if tipo_captura == "Rápido / Actual":
            c1, c2 = st.columns([1, 2])
            with c1:
                b1, b2, b3 = st.columns(3)
                if b1.button("+10"): piezas_sumar = 10
                if b2.button("+50"): piezas_sumar = 50
                if b3.button("+100"): piezas_sumar = 100
            with c2:
                cantidad_manual = st.number_input("Cantidad:", min_value=0, value=0, step=1)
                if st.button("Guardar", type="primary"):
                    piezas_sumar = cantidad_manual
        else:
            f_pasada = st.date_input("Fecha:", value=date.today())
            h_pasada = st.time_input("Hora:", value=datetime.now().time())
            cantidad_pasada = st.number_input("Cantidad:", min_value=1, value=10, step=1)
            fecha_registro = f_pasada.strftime("%Y-%m-%d")
            hora_registro = h_pasada.strftime("%H:%M:%S")
            if st.button("Guardar Registro Pasado", type="primary"):
                piezas_sumar = cantidad_pasada

        obs = st.text_input("Observaciones del Turno:", placeholder="Ej. Ajuste en prensa...")
        if piezas_sumar > 0:
            insertar_registro(oc_actual, fecha_registro, hora_registro, piezas_sumar, obs if obs else "Sin observaciones")
            st.success(f"✅ ¡Registradas {piezas_sumar} piezas!")
            st.rerun()

    st.markdown("---")
    st.subheader(f"📋 Historial en Nube - {oc_actual}")
    if not df_oc.empty:
        st.dataframe(df_oc.sort_values(by="id", ascending=False), use_container_width=True)
        with st.expander("✏️ Editar o Eliminar un Registro de Producción"):
            id_sel = st.selectbox("Selecciona ID:", df_oc["id"].tolist())
            row_sel = df_oc[df_oc["id"] == id_sel].iloc[0]
            
            c_e1, c_e2 = st.columns(2)
            p_edit = c_e1.number_input("Piezas corregidas:", min_value=0, value=int(row_sel["piezas_producidas"]))
            obs_edit = c_e2.text_input("Obs corregidas:", value=str(row_sel["observaciones_turno"]))
            
            cb1, cb2 = st.columns(2)
            if cb1.button("💾 Guardar Cambios"):
                actualizar_registro_supabase(id_sel, p_edit, obs_edit)
                st.success("Actualizado")
                st.rerun()
            if cb2.button("🗑️ Eliminar Registro"):
                eliminar_registro_supabase(id_sel)
                st.success("Eliminado")
                st.rerun()

elif menu_seleccionado == "📄 Generador de Remisiones":
    st.subheader("Generador de Remisiones Oficiales - Formato Original Crealag")
    df_oc_rem = df[df["orden_compra"] == oc_actual] if not df.empty else pd.DataFrame()
    piezas_producidas_total = df_oc_rem["piezas_producidas"].sum() if not df_oc_rem.empty else 0
    
    st.info(f"📦 **Estado de Almacén para `{oc_actual}`:** Total Producido: **{piezas_producidas_total} piezas**.")

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
        pdf_buffer = generar_pdf_original(atencion, compania, puesto, email, cel, referencia, oc_actual, fecha_remision, cantidad_piezas, fecha_recibido_str)
        st.success("¡Remisión generada con éxito!")
        st.download_button(label="📥 Descargar Remisión en PDF", data=pdf_buffer, file_name="Remision.pdf", mime="application/pdf")