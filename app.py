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

# Estilos CSS - Paleta Oscura Neutra con Tabla Estilizada y Amigable
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

df_ocs_catalogo = cargar_catalogo_ocs()
df = cargar_datos_supabase()

# --- FUNCIÓN DE CÁLCULO DE MATERIALES Y GENERACIÓN DE EXCEL ---
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
            "Consumo Exacto": round(exacto, 2),
            "Cantidad a Comprar (Enteros)": int(a_comprar),
            "P.U. c/IVA ($)": it["PU_cIVA"],
            "Total c/IVA ($)": total,
            "Proveedor": it["Proveedor"]
        })
    return pd.DataFrame(filas)

def generar_excel_costeo(df_costeo, meta_pzas, oc_ref, proveedor_acero):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_principal = df_costeo[df_costeo["Categoría"] == "Material Principal"].drop(columns=["Categoría"])
        df_consumibles = df_costeo[df_costeo["Categoría"] == "Consumible"].drop(columns=["Categoría"])
        
        df_costeo.to_excel(writer, sheet_name="Requerimiento_Compras", index=False, startrow=4)
        ws = writer.sheets["Requerimiento_Compras"]
        ws.write("A1", f"CREALAG - EXPLOSIÓN DE MATERIALES Y COSTEO (OC: {oc_ref})")
        ws.write("A2", f"Meta de Producción: {meta_pzas:,} piezas | Proveedor Acero: {proveedor_acero} | Fecha: {date.today().strftime('%d/%m/%Y')}")
        
        ultima_fila = 5 + len(df_costeo) + 1
        ws.write(f"E{ultima_fila}", "TOTAL GENERAL c/IVA:")
        ws.write_formula(f"F{ultima_fila}", f"=SUM(F6:F{ultima_fila-1})")
        
        df_principal.to_excel(writer, sheet_name="Desglose_Detallado", index=False, startrow=2)
        ws2 = writer.sheets["Desglose_Detallado"]
        ws2.write("A1", f"MATERIAL PRINCIPAL PARA {meta_pzas:,} PIEZAS")
        
        fila_inicio_cons = 2 + len(df_principal) + 4
        ws2.write(f"A{fila_inicio_cons-1}", "DESGLOSE DE CONSUMIBLES")
        df_consumibles.to_excel(writer, sheet_name="Desglose_Detallado", index=False, startrow=fila_inicio_cons)

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
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 2