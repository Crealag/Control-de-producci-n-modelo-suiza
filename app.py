import streamlit as st
import pandas as pd
import math
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

# Estilos CSS - Diseño Moderno, Limpio y Ejecutivo (Paleta Oscura Crealag)
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
[data-testid="stMetricValue"] { color: #38BDF8 !important; font-weight: 800 !important; font-size: 26px !important; }
[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-weight: 600 !important; font-size: 13px !important; }

/* Tarjetas contenedoras limpias */
.css-1r6slb0, div.stHorizontalBlock {
    background-color: #111B2E;
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 15px;
}

/* Estilos amigables y modernos para la tabla de datos */
[data-testid="stDataFrame"] {
    border: 1px solid #334155;
    border-radius: 12px;
    overflow: hidden;
    background-color: #111B2E;
}
[data-testid="stDataFrame"] th {
    background-color: #1E293B !important;
    color: #38BDF8 !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}
[data-testid="stDataFrame"] td {
    color: #F1F5F9 !important;
    font-size: 13.5px !important;
}
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

# Funciones para Tablas Independientes (Compras vs Cambios de Consumibles por Ciclo)
def cargar_historial_compras():
    if not supabase:
        return pd.DataFrame(columns=["id", "fecha", "material", "cantidad", "proveedor", "costo_total", "observaciones"])
    try:
        res = supabase.table("Historial_Compras_Materiales").select("*").order("fecha", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "fecha", "material", "cantidad", "proveedor", "costo_total", "observaciones"])
    except Exception:
        return pd.DataFrame(columns=["id", "fecha", "material", "cantidad", "proveedor", "costo_total", "observaciones"])

def registrar_compra_material(fecha, material, cantidad, proveedor, costo_total, observaciones):
    if not supabase: return False
    try:
        supabase.table("Historial_Compras_Materiales").insert({
            "fecha": fecha, "material": material, "cantidad": float(cantidad),
            "proveedor": proveedor, "costo_total": float(costo_total), "observaciones": observaciones
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar compra: {e}")
        return False

def eliminar_compra_material(record_id):
    if not supabase: return
    try:
        supabase.table("Historial_Compras_Materiales").delete().eq("id", record_id).execute()
    except Exception as e:
        st.error(f"Error al eliminar compra: {e}")

def cargar_historial_cambios():
    if not supabase:
        return pd.DataFrame(columns=["id", "fecha", "operacion", "consumible", "piezas_acumuladas_corte", "piezas_del_ciclo", "observaciones"])
    try:
        res = supabase.table("Historial_Cambios_Consumibles").select("*").order("fecha", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "fecha", "operacion", "consumible", "piezas_acumuladas_corte", "piezas_del_ciclo", "observaciones"])
    except Exception:
        return pd.DataFrame(columns=["id", "fecha", "operacion", "consumible", "piezas_acumuladas_corte", "piezas_del_ciclo", "observaciones"])

def registrar_cambio_consumible(fecha, operacion, consumible, piezas_corte, piezas_ciclo, observaciones):
    if not supabase: return False
    try:
        supabase.table("Historial_Cambios_Consumibles").insert({
            "fecha": fecha, 
            "operacion": operacion, 
            "consumible": consumible,
            "piezas_acumuladas_corte": int(piezas_corte),
            "piezas_del_ciclo": int(piezas_ciclo),
            "observaciones": observaciones
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar cambio: {e}")
        return False

def eliminar_cambio_consumible(record_id):
    if not supabase: return
    try:
        supabase.table("Historial_Cambios_Consumibles").delete().eq("id", record_id).execute()
    except Exception as e:
        st.error(f"Error al eliminar cambio: {e}")

df_ocs_catalogo = cargar_catalogo_ocs()
df = cargar_datos_supabase()
df_compras = cargar_historial_compras()
df_cambios = cargar_historial_cambios()

# --- FUNCIÓN DE CÁLCULO DE MATERIALES (Base 1,700 pzas) Y EXPORTACIÓN ---
def calcular_requerimiento_materiales(meta_pzas, proveedor_acero="ACEROMEX"):
    BASE_PIEZAS = 1700.0
    
    pu_semiflecha = 39.47 if proveedor_acero == "ACEROMEX" else 45.78
    pu_solera = 55.81 if proveedor_acero == "ACEROMEX" else 53.57
    
    items = [
        {"Categoría": "Material Principal", "Concepto": 'Semiflecha 1/4"', "Base_1700": 1340, "PU_cIVA": pu_semiflecha, "Proveedor": proveedor_acero},
        {"Categoría": "Material Principal", "Concepto": 'Solera 1/8" x 1/2"', "Base_1700": 230, "PU_cIVA": pu_solera, "Proveedor": proveedor_acero},
        {"Categoría": "Material Principal", "Concepto": "Gas CO2 25 Kg", "Base_1700": 7, "PU_cIVA": 950.00, "Proveedor": "PROVEEDOR GAS"},
        {"Categoría": "Material Principal", "Concepto": "Soldadura 5 Kg", "Base_1700": 12, "PU_cIVA": 360.40, "Proveedor": "RUEDAS Y RODAJAS"},
        {"Categoría": "Consumible", "Concepto": 'Disco de corte 4 1/2"', "Base_1700": 34, "PU_cIVA": 12.18, "Proveedor": "RUEDAS Y RODAJAS"},
        {"Categoría": "Consumible", "Concepto": "Disco de lija", "Base_1700": 34, "PU_cIVA": 44.08, "Proveedor": "RUEDAS Y RODAJAS"},
        {"Categoría": "Consumible", "Concepto": 'Disco de corte 14"', "Base_1700": 19, "PU_cIVA": 67.28, "Proveedor": "RUEDAS Y RODAJAS"},
        {"Categoría": "Consumible", "Concepto": 'Broca 3/16"', "Base_1700": 13, "PU_cIVA": 28.00, "Proveedor": "RUEDAS Y RODAJAS"},
        {"Categoría": "Consumible", "Concepto": "Cintas de aislar", "Base_1700": 18, "PU_cIVA": 20.00, "Proveedor": "RUEDAS Y RODAJAS"},
    ]
    
    filas = []
    for it in items:
        exacto = (it["Base_1700"] / BASE_PIEZAS) * meta_pzas
        a_comprar = math.ceil(exacto) if meta_pzas > 0 else 0
        total = round(a_comprar * it["PU_cIVA"], 2)
        filas.append({
            "Categoría": it["Categoría"],
            "Concepto": it["Concepto"],
            "Consumo Teórico": round(exacto, 2),
            "A Comprar (Cerrado)": int(a_comprar),
            "P.U. c/IVA ($)": float(it["PU_cIVA"]),
            "Subtotal c/IVA ($)": float(total),
            "Proveedor": it["Proveedor"]
        })
    return pd.DataFrame(filas)

def generar_excel_costeo(df_costeo, meta_pzas, oc_ref, proveedor_acero):
    buffer = BytesIO()
    header_info = f"CREALAG - EXPLOSIÓN DE MATERIALES Y COSTEO (OC: {oc_ref})\n"
    meta_info = f"Meta de Producción: {meta_pzas} piezas | Proveedor Acero: {proveedor_acero} | Fecha: {date.today().strftime('%d/%m/%Y')}\n\n"
    
    csv_bytes = df_costeo.to_csv(index=False).encode('utf-8-sig')
    
    buffer.write(header_info.encode('utf-8-sig'))
    buffer.write(meta_info.encode('utf-8-sig'))
    buffer.write(csv_bytes)
    
    buffer.seek(0)
    return buffer

# --- FUNCIÓN GENERADORA DE PDF ---
def generar_pdf_original(atencion, compania, puesto, email, cel, referencia, oc_actual, fecha_remision, cantidad_piezas):
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
    
    texto_cuerpo = f"Referente a su pedido <b><u>{oc_actual}</u></b>. Se hace entrega de <b><u>{cantidad_piezas}</u></b> piezas de respaldo de silla <b><u>modelo Suiza</u></b>."
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
    
    menu_seleccionado = st.selectbox(
        "Navegación del Sistema", 
        ["📊 Producción y Registro", "💰 Costeo y Materiales (Excel)", "📄 Generador de Remisiones"]
    )
    st.markdown("---")
    
    st.header("📦 Órdenes de Compra")
    lista_ocs = df_ocs_catalogo["orden_compra"].tolist() if not df_ocs_catalogo.empty else ["HC-0505"]
    oc_actual = st.selectbox("Seleccionar OC Activa:", lista_ocs)
    
    row_oc_info = df_ocs_catalogo[df_ocs_catalogo["orden_compra"] == oc_actual].iloc[0] if not df_ocs_catalogo.empty and oc_actual in df_ocs_catalogo["orden_compra"].values else {"meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}
    meta_actual = int(row_oc_info.get("meta_piezas", 1700))
    estado_oc = str(row_oc_info.get("estado", "Activa"))
    entregadas_actual = int(row_oc_info.get("piezas_entregadas", 0) if pd.notnull(row_oc_info.get("piezas_entregadas")) else 0)
    
    df_oc_sidebar_check = df[df["orden_compra"] == oc_actual] if not df.empty else pd.DataFrame()
    producido_sidebar_check = df_oc_sidebar_check["piezas_producidas"].sum() if not df_oc_sidebar_check.empty else 0

    if producido_sidebar_check >= meta_actual and estado_oc == "Activa":
        actualizar_oc_supabase(oc_actual, meta_actual, "Cerrada", entregadas_actual)
        estado_oc = "Cerrada"

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

    if piezas_producidas_oc >= meta_actual and estado_oc == "Activa":
        actualizar_oc_supabase(oc_actual, meta_actual, "Cerrada", entregadas_actual)
        estado_oc = "Cerrada"

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
        piezas_restantes = max(0, meta_actual - piezas_producidas_oc)
        
        if piezas_restantes == 0:
            st.success(f"🎉 ¡La Orden `{oc_actual}` ya ha completado el 100% de su meta de producción ({meta_actual} pzas)!")
        else:
            with st.form("form_registro_produccion"):
                col_p1, col_p2 = st.columns([1, 2])
                with col_p1:
                    cantidad_piezas_in = st.number_input(
                        "Cantidad de Piezas:", 
                        min_value=1, 
                        max_value=int(piezas_restantes), 
                        value=min(10, int(piezas_restantes)), 
                        step=1
                    )
                with col_p2:
                    obs_in = st.text_input("Observaciones del Turno:", placeholder="Ej. Avance turno mañana...")
                
                col_d1, col_d2 = st.columns(2)
                fecha_in = col_d1.date_input("Fecha de Registro:", value=date.today())
                hora_in = col_d2.time_input("Hora de Registro:", value=datetime.now().time())
                
                btn_registrar = st.form_submit_button("⚡ Registrar Piezas Producidas", type="primary", use_container_width=True)
                if btn_registrar:
                    if cantidad_piezas_in > piezas_restantes:
                        st.error(f"❌ No puedes rebasar la meta. Solo faltan {piezas_restantes} piezas para completar los {meta_actual} pzas.")
                    else:
                        f_str = fecha_in.strftime("%Y-%m-%d")
                        h_str = hora_in.strftime("%I:%M %p")
                        insertar_registro(oc_actual, f_str, h_str, cantidad_piezas_in, obs_in if obs_in else "Sin observaciones")
                        st.success(f"✅ ¡Registradas {cantidad_piezas_in} piezas a las {h_str}!")
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("⚠️ Registrar Paro o Incidencia en Línea")
        with st.form("form_registro_paro"):
            col_paro1, col_paro2 = st.columns(2)
            with col_paro1:
                motivo_paro = st.selectbox("Motivo del Paro:", [
                    "Paro por falta de material", 
                    "Paro por mantenimiento preventivo/correctivo", 
                    "Paro por falta de energía / servicios", 
                    "Cambio de modelo / herramental", 
                    "Otro motivo"
                ])
            with col_paro2:
                horas_paro = st.number_input("Duración del Paro (Horas):", min_value=0.25, max_value=24.0, value=1.0, step=0.25)
            
            detalle_paro = st.text_input("Detalles adicionales del paro:", placeholder="Ej. Ajuste de dados en línea 2...")
            
            col_fd1, col_fd2 = st.columns(2)
            fecha_paro = col_fd1.date_input("Fecha del Paro:", value=date.today(), key="fecha_paro_key")
            hora_paro = col_fd2.time_input("Hora del Paro:", value=datetime.now().time(), key="hora_paro_key")
            
            btn_paro = st.form_submit_button("🚨 Registrar Paro / Incidencia", type="primary", use_container_width=True)
            if btn_paro:
                f_str_p = fecha_paro.strftime("%Y-%m-%d")
                h_str_p = hora_paro.strftime("%I:%M %p")
                texto_observacion = f"[PARO: {motivo_paro} | Duración: {horas_paro} hrs] {detalle_paro}" if detalle_paro else f"[PARO: {motivo_paro} | Duración: {horas_paro} hrs]"
                insertar_registro(oc_actual, f_str_p, h_str_p, 0, texto_observacion)
                st.warning(f"⚠️ Paro registrado correctamente por {horas_paro} hrs ({motivo_paro}).")
                st.rerun()

    st.markdown("---")
    st.subheader(f"📋 Historial y Ritmo de Producción - {oc_actual}")
    
    if not df_oc.empty:
        df_solo_produccion = df_oc[df_oc["piezas_producidas"] > 0].copy()
        
        if not df_solo_produccion.empty:
            df_solo_produccion['fecha_str'] = df_solo_produccion['fecha'].astype(str)
            df_diario = df_solo_produccion.groupby('fecha_str', as_index=False)['piezas_producidas'].sum().sort_values('fecha_str')
            df_diario.columns = ['Fecha', 'Piezas Producidas']
            
            st.markdown("#### 📊 Ritmo de Producción Diaria (Tendencia)")
            st.line_chart(df_diario, x='Fecha', y='Piezas Producidas', use_container_width=True)
        else:
            st.info("ℹ️ Aún no hay registros de producción con piezas para mostrar en la gráfica (solo paros registrados).")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📄 Registros Detallados (Producción y Paros)")
        
        df_mostrar = df_oc.sort_values(by="id", ascending=False)
        st.dataframe(
            df_mostrar,
            use_container_width=True,
            hide_index=True,
            column_order=["id", "orden_compra", "fecha", "hora", "piezas_producidas", "observaciones_turno"],
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "orden_compra": st.column_config.TextColumn("Orden de Compra", width="medium"),
                "fecha": st.column_config.TextColumn("Fecha", width="medium"),
                "hora": st.column_config.TextColumn("Hora", width="small"),
                "piezas_producidas": st.column_config.NumberColumn("Piezas Producidas", format="%d pzas", width="medium"),
                "observaciones_turno": st.column_config.TextColumn("Observaciones / Paros", width="large")
            }
        )
        
        with st.expander("✏️ Editar o Eliminar un Registro"):
            id_sel = st.selectbox("Selecciona ID:", df_oc["id"].tolist())
            row_sel = df_oc[df_oc["id"] == id_sel].iloc[0]
            
            c_e1, c_e2 = st.columns(2)
            p_edit = c_e1.number_input("Piezas corregidas:", min_value=0, value=int(row_sel["piezas_producidas"]))
            obs_edit = c_e2.text_input("Obs / Paro corregido:", value=str(row_sel["observaciones_turno"]))
            
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
        st.info("Aún no hay registros para esta orden.")

elif menu_seleccionado == "💰 Costeo y Materiales (Excel)":
    st.subheader(f"💰 Explosión de Materiales y Costeo — Ref: {oc_actual}")
    st.markdown("Gestiona tus costos de orden, tu plan de compras semanal o lleva el registro independiente de compras y cambios de consumibles.")

    # --- SELECTOR DE VISTA ESTILO PESTAÑA LIMPIA ---
    modo_vista = st.radio(
        "Modo de Planificación:",
        [
            "📦 Costeo Total Orden Activa", 
            "🗓️ Plan de Compras Semanal", 
            "🛒 Registro de Compras (Varilla / Solera)", 
            "🔄 Control de Cambios y Rendimiento por Ciclo (Gas / Soldadura)"
        ],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("---")

    if modo_vista == "📦 Costeo Total Orden Activa":
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            meta_costeo = meta_actual
            st.metric(label="Meta de Piezas (Orden Activa)", value=f"{meta_costeo:,} pzas")
        with col_c2:
            proveedor_sel = st.selectbox(
                "Proveedor Principal de Acero (Semiflecha y Solera):", 
                ["ACEROMEX", "VENTACERO"],
                key="prov_gen"
            )

        df_base = calcular_requerimiento_materiales(meta_costeo, proveedor_sel)

        st.markdown("#### 📋 Lista Interactiva de Requerimiento para Compras (Total Orden)")
        st.caption("💡 **Consejo:** Haz doble clic en cualquier celda para editar textos, cambiar precios (`P.U. c/IVA`) o cantidades. Usa el botón `+` para agregar nuevos materiales o la papelera para borrarlos.")

        df_editado = st.data_editor(
            df_base,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="editor_costeo_general",
            column_config={
                "Categoría": st.column_config.SelectboxColumn("Categoría", options=["Material Principal", "Consumible", "Herramental", "Otro"], required=True),
                "Concepto": st.column_config.TextColumn("Concepto / Material", required=True),
                "Consumo Teórico": st.column_config.NumberColumn("Consumo Teórico", format="%.2f"),
                "A Comprar (Cerrado)": st.column_config.NumberColumn("A Comprar (Cerrado)", format="%d u.", min_value=0, step=1, required=True),
                "P.U. c/IVA ($)": st.column_config.NumberColumn("P.U. c/IVA ($)", format="$%.2f", min_value=0.0, step=0.5, required=True),
                "Subtotal c/IVA ($)": st.column_config.NumberColumn("Subtotal c/IVA ($)", format="$%,.2f"),
                "Proveedor": st.column_config.TextColumn("Proveedor")
            }
        )

        df_editado["Subtotal c/IVA ($)"] = df_editado["A Comprar (Cerrado)"] * df_editado["P.U. c/IVA ($)"]

        costo_material_principal = df_editado[df_editado["Categoría"] == "Material Principal"]["Subtotal c/IVA ($)"].sum()
        costo_consumibles = df_editado[df_editado["Categoría"].isin(["Consumible", "Herramental", "Otro"])]["Subtotal c/IVA ($)"].sum()
        costo_total_general = df_editado["Subtotal c/IVA ($)"].sum()
        costo_unitario_pza = costo_total_general / meta_costeo if meta_costeo > 0 else 0

        st.markdown("<br>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Material Principal (c/IVA)", f"${costo_material_principal:,.2f}")
        k2.metric("Consumibles / Otros (c/IVA)", f"${costo_consumibles:,.2f}")
        k3.metric("Inversión Total Compra", f"${costo_total_general:,.2f}")
        k4.metric("Costo Directo / Pieza", f"${costo_unitario_pza:,.2f}")

        st.markdown("---")
        excel_buffer_general = generar_excel_costeo(df_editado, meta_costeo, oc_actual, proveedor_sel)
        st.download_button(
            label="📥 Descargar Costeo Total de OC (.csv)",
            data=excel_buffer_general,
            file_name=f"Costeo_General_{oc_actual}_{meta_costeo}pzas.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )

    elif modo_vista == "🗓️ Plan de Compras Semanal":
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            piezas_diarias = st.number_input("Producción Diaria (pzas/día):", min_value=1, value=110, step=5)
        with col_s2:
            dias_semana = st.number_input("Días Laborales / Semana:", min_value=1, max_value=7, value=6, step=1)
        with col_s3:
            proveedor_sel_sem = st.selectbox(
                "Proveedor Acero Semanal:", 
                ["ACEROMEX", "VENTACERO"],
                key="prov_sem"
            )

        meta_semanal = piezas_diarias * dias_semana
        st.info(f"📅 Producción semanal objetivo: **{meta_semanal:,} piezas** ({piezas_diarias} pzas/día × {dias_semana} días).")

        df_semanal_base = calcular_requerimiento_materiales(meta_semanal, proveedor_sel_sem)

        st.markdown("#### 📋 Plan de Compras por Ritmo de Producción Semanal")
        st.caption("💡 Edita precios unitarios o cantidades según tus cotizaciones actuales con proveedores.")

        df_semanal_editado = st.data_editor(
            df_semanal_base,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="editor_compras_semanal",
            column_config={
                "Categoría": st.column_config.SelectboxColumn("Categoría", options=["Material Principal", "Consumible", "Herramental", "Otro"], required=True),
                "Concepto": st.column_config.TextColumn("Concepto / Material", required=True),
                "Consumo Teórico": st.column_config.NumberColumn("Consumo Teórico", format="%.2f"),
                "A Comprar (Cerrado)": st.column_config.NumberColumn("A Comprar Semanal", format="%d u.", min_value=0, step=1, required=True),
                "P.U. c/IVA ($)": st.column_config.NumberColumn("P.U. c/IVA ($)", format="$%.2f", min_value=0.0, step=0.5, required=True),
                "Subtotal c/IVA ($)": st.column_config.NumberColumn("Subtotal Semanal ($)", format="$%,.2f"),
                "Proveedor": st.column_config.TextColumn("Proveedor")
            }
        )

        df_semanal_editado["Subtotal c/IVA ($)"] = df_semanal_editado["A Comprar (Cerrado)"] * df_semanal_editado["P.U. c/IVA ($)"]
        gasto_total_semanal = df_semanal_editado["Subtotal c/IVA ($)"].sum()

        st.markdown("<br>", unsafe_allow_html=True)
        st.metric(label="Inversión Total Estimada para Compras de la Semana", value=f"${gasto_total_semanal:,.2f}")

        st.markdown("---")
        excel_buffer_semanal = generar_excel_costeo(df_semanal_editado, meta_semanal, f"SEMANAL-{oc_actual}", proveedor_sel_sem)
        st.download_button(
            label="📥 Descargar Plan de Compras Semanal (.csv)",
            data=excel_buffer_semanal,
            file_name=f"Plan_Compras_Semanal_{meta_semanal}pzas.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )

    elif modo_vista == "🛒 Registro de Compras (Varilla / Solera)":
        st.markdown("#### 🛒 Historial de Compras Semanales (Acero y Materia Prima)")
        st.caption("Registra tus compras fijas semanales de semiflecha, solera u otros materiales con sus costos y proveedores reales.")

        with st.form("form_reg_compra_material"):
            c_m1, c_m2, c_m3 = st.columns(3)
            fecha_com = c_m1.date_input("Fecha de Compra:", value=date.today())
            material_com = c_m2.selectbox("Material:", ['Semiflecha 1/4"', 'Solera 1/8" x 1/2"', "Otro Material Principal"])
            cantidad_com = c_m3.number_input("Cantidad Comprada:", min_value=1.0, value=1.0, step=1.0)

            c_m4, c_m5 = st.columns(2)
            proveedor_com = c_m4.text_input("Proveedor:", value="ACEROMEX")
            costo_com = c_m5.number_input("Costo Total c/IVA ($):", min_value=0.0, value=0.0, step=100.0)

            obs_com = st.text_input("Observaciones / Factura:", placeholder="Ej. Compra semanal programada...")

            btn_guardar_com = st.form_submit_button("💾 Guardar Compra de Material", type="primary", use_container_width=True)
            if btn_guardar_com:
                if registrar_compra_material(fecha_com.strftime("%Y-%m-%d"), material_com, cantidad_com, proveedor_com, costo_com, obs_com):
                    st.success("✅ ¡Compra de material registrada con éxito!")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### 📜 Historial de Compras Registradas")
        if not df_compras.empty:
            st.dataframe(
                df_compras,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "fecha": st.column_config.TextColumn("Fecha", width="medium"),
                    "material": st.column_config.TextColumn("Material", width="large"),
                    "cantidad": st.column_config.NumberColumn("Cantidad", format="%.1f u."),
                    "proveedor": st.column_config.TextColumn("Proveedor", width="medium"),
                    "costo_total": st.column_config.NumberColumn("Costo Total", format="$%,.2f"),
                    "observaciones": st.column_config.TextColumn("Observaciones", width="large"),
                }
            )
            with st.expander("🗑️ Eliminar Registro de Compra"):
                id_del_c = st.selectbox("Selecciona ID a borrar:", df_compras["id"].tolist(), key="del_c")
                if st.button("Borrar Compra Seleccionada"):
                    eliminar_compra_material(id_del_c)
                    st.success("Compra eliminada.")
                    st.rerun()
        else:
            st.info("ℹ️ Aún no hay compras registradas.")

    else:
        st.markdown("#### 🔄 Control de Cambios y Rendimiento por Ciclo (Gas y Soldadura)")
        st.caption("Registra cuándo se agota un insumo y el sistema calculará automáticamente cuántas piezas exactas rindió en ese ciclo para esa operación.")

        with st.form("form_reg_cambio_consumible"):
            c_g1, c_g2, c_g3 = st.columns(3)
            fecha_cam = c_g1.date_input("Fecha del Cambio:", value=date.today())
            operacion_cam = c_g2.selectbox("Operación / Línea:", ["Operación 1 (Línea 1)", "Operación 2 (Línea 2)"])
            consumible_cam = c_g3.selectbox("Consumible:", ["Gas CO2 25 Kg", "Soldadura 5 Kg", "Otro Consumible"])

            c_g4, c_g5 = st.columns(2)
            piezas_corte = c_g4.number_input(
                "Piezas acumuladas al momento del cambio:", 
                min_value=0, 
                value=100, 
                step=1,
                help="Número total de piezas producidas hasta la hora exacta en que se terminó el tanque o la soldadura."
            )
            obs_cam = c_g5.text_input("Observaciones / Motivo:", placeholder="Ej. Se terminó a mitad de turno...")

            btn_guardar_cam = st.form_submit_button("⚡ Registrar Cambio y Calcular Rendimiento", type="primary", use_container_width=True)
            if btn_guardar_cam:
                # Calcular piezas del ciclo restando el corte anterior para este mismo consumible y operación
                df_op_cons = df_cambios[(df_cambios["operacion"] == operacion_cam) & (df_cambios["consumible"] == consumible_cam)]
                if not df_op_cons.empty:
                    ultima_pieza_anterior = df_op_cons.iloc[0]["piezas_acumuladas_corte"]
                    piezas_ciclo = max(0, piezas_corte - ultima_pieza_anterior)
                else:
                    piezas_ciclo = piezas_corte  # Primer registro para este consumible

                if registrar_cambio_consumible(fecha_cam.strftime("%Y-%m-%d"), operacion_cam, consumible_cam, piezas_corte, piezas_ciclo, obs_cam):
                    st.success(f"✅ ¡Cambio registrado! Este ciclo rindió **{piezas_ciclo:,} piezas**.")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### 📜 Historial de Cambios y Rendimiento por Ciclo")
        if not df_cambios.empty:
            st.dataframe(
                df_cambios,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "fecha": st.column_config.TextColumn("Fecha", width="medium"),
                    "operacion": st.column_config.TextColumn("Operación", width="medium"),
                    "consumible": st.column_config.TextColumn("Consumible", width="large"),
                    "piezas_acumuladas_corte": st.column_config.NumberColumn("Pz. Acumuladas Corte", format="%d pzas"),
                    "piezas_del_ciclo": st.column_config.NumberColumn("⚡ Rendimiento del Ciclo", format="%d pzas"),
                    "observaciones": st.column_config.TextColumn("Observaciones", width="large"),
                }
            )
            with st.expander("🗑️ Eliminar Registro de Cambio"):
                id_del_g = st.selectbox("Selecciona ID a borrar:", df_cambios["id"].tolist(), key="del_g")
                if st.button("Borrar Cambio Seleccionado"):
                    eliminar_cambio_consumible(id_del_g)
                    st.success("Cambio eliminado.")
                    st.rerun()
        else:
            st.info("ℹ️ Aún no hay registros de cambios con rendimiento por ciclo.")

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
            
            max_val_permitido = max(1, int(piezas_almacen_rem))
            cantidad_piezas_entrega = st.number_input(
                "Cantidad de piezas a entregar en esta remisión", 
                min_value=1, 
                max_value=max_val_permitido,
                value=max_val_permitido
            )

        sumar_a_entregadas = st.checkbox(" Descontar estas piezas de Almacén al generar remisión", value=True)
        submit_pdf = st.form_submit_button("Generar PDF de Remisión Original", type="primary")

    if submit_pdf:
        if piezas_almacen_rem <= 0:
            st.error("❌ No hay piezas disponibles en almacén para remitir en esta Orden de Compra.")
        elif cantidad_piezas_entrega > piezas_almacen_rem:
            st.error(f"❌ No puedes remitir {cantidad_piezas_entrega} piezas. Solo hay {piezas_almacen_rem} piezas disponibles en almacén.")
        else:
            if sumar_a_entregadas:
                registrar_entrega_piezas(oc_actual, cantidad_piezas_entrega)
            pdf_buffer = generar_pdf_original(atencion, compania, puesto, email, cel, referencia, oc_actual, fecha_remision, cantidad_piezas_entrega)
            st.success(f"¡Remisión por {cantidad_piezas_entrega} piezas generada con éxito y descontada del almacén!")
            st.download_button(label="📥 Descargar Remisión en PDF", data=pdf_buffer, file_name="Remision.pdf", mime="application/pdf")