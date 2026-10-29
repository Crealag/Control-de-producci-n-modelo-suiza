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

# --- CREDENCIALES ---
SUPABASE_URL = "https://jdihosehcvvzxsbhnqvf.supabase.co"
SUPABASE_KEY = "sb_publishable_D79R2pyWt6LI3lggygrbjg_4oJmoEX_"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = init_supabase()

# Estilos CSS - Paleta Oscura Neutra
css_estilos = """
<style>
.stApp { background-color: #0A0F1D; color: #F8FAFC; }
[data-testid="stSidebar"] { background-color: #111B2E; border-right: 1px solid #1E293B; }
div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
    background-color: #1A263D !important; color: #F8FAFC !important; border-color: #334155 !important;
}
button, .stButton>button, [data-testid="baseButton-primary"], div.stButton>button {
    background-color: #1E293B !important;
    color: #F8FAFC !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
button:hover, .stButton>button:hover, [data-testid="baseButton-primary"]:hover {
    background-color: #2D3E5E !important;
    border-color: #475569 !important;
    color: #FFFFFF !important;
}
.brand-title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800; color: #F8FAFC; }
[data-testid="stMetricValue"] { color: #F8FAFC !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-weight: 700 !important; }
</style>
"""
st.markdown(css_estilos, unsafe_allow_html=True)

# --- FUNCIONES DE BASE DE DATOS SEGURAS ---
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

def guardar_nueva_oc(orden, meta):
    if not supabase: return False
    try:
        supabase.table("Órdenes_Compra").insert({"orden_compra": orden, "meta_piezas": int(meta), "estado": "Activa", "piezas_entregadas": 0}).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar nueva OC: {e}")
        return False

def actualizar_oc_supabase(orden, meta, estado, entregadas):
    if not supabase: return False
    try:
        supabase.table("Órdenes_Compra").update({"meta_piezas": int(meta), "estado": estado, "piezas_entregadas": int(entregadas)}).eq("orden_compra", orden).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar la OC: {e}")
        return False

def registrar_entrega_piezas(orden, cantidad_entregada_nueva):
    if not supabase: return False
    try:
        res = supabase.table("Órdenes_Compra").select("piezas_entregadas").eq("orden_compra", orden).execute()
        actuales = res.data[0]["piezas_entregadas"] if res.data and res.data[0]["piezas_entregadas"] is not None else 0
        total_acumulado = actuales + int(cantidad_entregada_nueva)
        supabase.table("Órdenes_Compra").update({"piezas_entregadas": total_acumulado}).eq("orden_compra", orden).execute()
        return True
    except Exception as e:
        st.error(f"Error al registrar entrega: {e}")
        return False

def eliminar_oc_supabase(orden):
    if not supabase: return False
    try:
        supabase.table("Órdenes_Compra").delete().eq("orden_compra", orden).execute()
        supabase.table("Producción").delete().eq("orden_compra", orden).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar la OC: {e}")
        return False

def cargar_datos_supabase():
    if not supabase:
        return pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])
    try:
        res = supabase.table("Producción").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])
    except Exception:
        return pd.DataFrame(columns=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"])

def insertar_registro(orden, fecha, hora, piezas, observaciones):
    if not supabase: return
    try:
        supabase.table("Producción").insert({
            "orden_compra": orden, "fecha": fecha, "hora": hora,
            "piezas_producidas": int(piezas), "observaciones_turno": observaciones
        }).execute()
    except Exception as e:
        st.error(f"Error al insertar registro: {e}")

def actualizar_registro_supabase(record_id, piezas, observaciones):
    if not supabase: return
    try:
        supabase.table("Producción").update({"piezas_producidas": int(piezas), "observaciones_turno": observaciones}).eq("id", record_id).execute()
    except Exception as e:
        st.error(f"Error al actualizar registro: {e}")

def eliminar_registro_supabase(record_id):
    if not supabase: return
    try:
        supabase.table("Producción").delete().eq("id", record_id).execute()
    except Exception as e:
        st.error(f"Error al eliminar registro: {e}")

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
    
    texto_cuerpo = f"Referente a su pedido <b><u>{oc_actual}</u></b> recibido el <b><u>{fecha_recibido_str}</u></b>. Se hace entrega de <b><u>{cantidad_piezas}</u></b> piezas de respaldo de silla <b><u>modelo Suiza</u></b>."
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
    st.markdown("<h2 class='brand-title'>crealag</h2>", unsafe_allow_html=True)
    st.caption("Fabricante mueblerio metalformado A.C. e INOX")
    st.markdown("---")
    
    menu_seleccionado = st.selectbox("Navegación del Sistema", ["📊 Producción y Registro", "📄 Generador de Remisiones"])
    st.markdown("---")
    
    st.header("📦 Órdenes de Compra")
    lista_ocs = df_ocs_catalogo["orden_compra"].tolist() if not df_ocs_catalogo.empty else ["HC-0505"]
    oc_actual = st.selectbox("Seleccionar OC Activa:", lista_ocs)
    
    row_oc_info = df_ocs_catalogo[df_ocs_catalogo["orden_compra"] == oc_actual].iloc[0] if not df_ocs_catalogo.empty and oc_actual in df_ocs_catalogo["orden_compra"].values else {"meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}
    meta_actual = int(row_oc_info.get("meta_piezas", 1700))
    estado_oc = str(row_oc_info.get("estado", "Activa"))
    entregadas_actual = int(row_oc_info.get("piezas_entregadas", 0) if pd.notnull(row_oc_info.get("piezas_entregadas")) else 0)
    
    if estado_oc == "Cerrada":
        st.error(f"🔒 OC `{oc_actual}` CERRADA (Solo lectura)")
    else:
        st.success(f"🟢 OC `{oc_actual}` Activa")

    with st.expander("➕ Registrar Nueva Orden de Compra"):
        nueva_oc_input = st.text_input("Nueva OC (Ej. HER-101026)")
        nueva_meta_input = st.number_input("Meta de piezas:", min_value=1, value=1700, step=10)
        if st.button("Guardar Nueva OC"):
            if nueva_oc_input and nueva_oc_input not in lista_ocs:
                if guardar_nueva_oc(nueva_oc_input, nueva_meta_input):
                    st.success(f"✅ OC `{nueva_oc_input}` registrada.")
                    st.rerun()

# --- VISTA PRINCIPAL ---
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Control de Producción y Remisiones</span></h1>", unsafe_allow_html=True)
st.markdown("---")

if menu_seleccionado == "📊 Producción y Registro":
    df_oc = df[df["orden_compra"] == oc_actual] if not df.empty else pd.DataFrame()
    piezas_producidas_oc = df_oc["piezas_producidas"].sum() if not df_oc.empty else 0
    piezas_almacen_actual = max(0, piezas_producidas_oc - entregadas_actual)
    porcentaje = min(1.0, piezas_producidas_oc / meta_actual) if meta_actual > 0 else 0.0

    st.subheader(f"Panel de Control - Orden Activa: {oc_actual} ({estado_oc})")
    
    with st.expander(f"⚙️ Configurar / Ajustar Orden {oc_actual}"):
        with st.form("form_edit_oc"):
            st.markdown("#### Ajustar Datos de la Orden")
            col_m1, col_m2, col_m3 = st.columns(3)
            meta_editada = col_m1.number_input("Meta de piezas:", min_value=1, value=meta_actual, step=10)
            entregadas_editadas = col_m2.number_input("Piezas Entregadas:", min_value=0, value=entregadas_actual, step=1)
            estado_editado = col_m3.selectbox("Estado de la OC:", ["Activa", "Cerrada"], index=0 if estado_oc == "Activa" else 1)
            
            btn_guardar_oc = st.form_submit_button("💾 Guardar Cambios en OC", type="primary")
            if btn_guardar_oc:
                if actualizar_oc_supabase(oc_actual, meta_editada, estado_editado, entregadas_editadas):
                    st.success(f"✅ OC {oc_actual} actualizada correctamente.")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### 🗑️ Zona de Peligro")
        if st.button("⚠️ Eliminar esta Orden de Compra por Completo", key="btn_del_oc_main"):
            if len(lista_ocs) > 1:
                if eliminar_oc_supabase(oc_actual):
                    st.success(f"🗑️ OC {oc_actual} eliminada por completo.")
                    st.rerun()
            else:
                st.error("No puedes eliminar la última Orden de Compra registrada.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Meta Estimada OC", f"{meta_actual} pzas")
    m2.metric("Producido Total", f"{piezas_producidas_oc} pzas")
    m3.metric("Entregadas / Remitidas", f"{entregadas_actual} pzas")
    m4.metric("Disponibles en Almacén", f"{piezas_almacen_actual} pzas")
    st.progress(porcentaje)

    st.markdown("---")

    if estado_oc != "Cerrada":
        st.subheader("➕ Registrar Piezas Producidas")
        
        with st.form("form_registro_produccion"):
            col_p1, col_p2 = st.columns([1, 2])
            with col_p1:
                cantidad_piezas_in = st.number_input("Cantidad de Piezas:", min_value=1, value=10, step=1)
            with col_p2:
                obs_in = st.text_input("Observaciones del Turno:", placeholder="Ej. Avance turno mañana...")
            
            col_d1, col_d2 = st.columns(2)
            fecha_in = col_d1.date_input("Fecha de Registro:", value=date.today())
            hora_in = col_d2.time_input("Hora de Registro:", value=datetime.now().time())
            
            btn_registrar = st.form_submit_button("⚡ Registrar Piezas Producidas", type="primary", use_container_width=True)
            if btn_registrar:
                f_str = fecha_in.strftime("%Y-%m-%d")
                h_str = hora_in.strftime("%I:%M %p")
                insertar_registro(oc_actual, f_str, h_str, cantidad_piezas_in, obs_in if obs_in else "Sin observaciones")
                st.success(f"✅ ¡Registradas {cantidad_piezas_in} piezas a las {h_str}!")
                st.rerun()

    st.markdown("---")
    st.subheader(f"📋 Historial y Ritmo de Producción - {oc_actual}")
    
    if not df_oc.empty:
        df_grafica = df_oc.copy()
        df_grafica['fecha_str'] = df_grafica['fecha'].astype(str)
        df_diario = df_grafica.groupby('fecha_str', as_index=False)['piezas_producidas'].sum().sort_values('fecha_str')
        df_diario.columns = ['Fecha', 'Piezas Producidas']
        
        st.markdown("#### 📊 Ritmo de Producción Diaria (Tendencia)")
        st.line_chart(df_diario, x='Fecha', y='Piezas Producidas', use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📄 Registros Detallados")
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
    else:
        st.info("Aún no hay registros de producción para esta orden.")

elif menu_seleccionado == "📄 Generador de Remisiones":
    st.subheader("Generador de Remisiones Oficiales - Formato Original Crealag")
    df_oc_rem = df[df["orden_compra"] == oc_actual] if not df.empty else pd.DataFrame()
    piezas_producidas_total = df_oc_rem["piezas_producidas"].sum() if not df_oc_rem.empty else 0
    piezas_almacen_rem = max(0, piezas_producidas_total - entregadas_actual)
    
    st.info(f"📦 **Estado de Almacén para `{oc_actual}`:** Total Producido: **{piezas_producidas_total} pzas** | Ya Entregadas: **{entregadas_actual} pzas** | Disponibles: **{piezas_almacen_rem} pzas**")

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
            cantidad_piezas_entrega = st.number_input(
                "Cantidad de piezas a entregar en esta remisión", 
                min_value=1, 
                value=max(1, int(piezas_almacen_rem))
            )

        meses_es = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        
        fecha_sugerida = f"{fecha_remision.day} de {meses_es[fecha_remision.month]} de {fecha_remision.year}"

        fecha_recibido_str = st.text_input("Fecha de pedido recibido (Texto)", value=fecha_sugerida)
        sumar_a_entregadas = st.checkbox(" Descontar estas piezas de Almacén al generar remisión", value=True)
        submit_pdf = st.form_submit_button("Generar PDF de Remisión Original", type="primary")

    if submit_pdf:
        if sumar_a_entregadas:
            registrar_entrega_piezas(oc_actual, cantidad_piezas_entrega)
        pdf_buffer = generar_pdf_original(atencion, compania, puesto, email, cel, referencia, oc_actual, fecha_remision, cantidad_piezas_entrega, fecha_recibido_str)
        st.success(f"¡Remisión por {cantidad_piezas_entrega} piezas generada con éxito y descontada del almacén!")
        st.download_button(label="📥 Descargar Remisión en PDF", data=pdf_buffer, file_name="Remision.pdf", mime="application/pdf")