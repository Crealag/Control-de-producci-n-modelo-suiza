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
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Estilos CSS - Paleta Oscura Neutra
css_estilos = """
<style>
.stApp { background-color: #0A0F1D; color: #F8FAFC; }
[data-testid="stSidebar"] { background-color: #111B2E; border-right: 1px solid #1E293B; }
div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
    background-color: #1A263D !important; color: #F8FAFC !important; border-color: #334155 !important;
}
button, .stButton>button, [data-testid="baseButton-primary"] {
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

# --- FUNCIONES DE BASE DE DATOS ---
def cargar_catalogo_ocs():
    try:
        res = supabase.table("Órdenes_Compra").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error al cargar catálogo: {e}")
    return pd.DataFrame([{"orden_compra": "HC-0505", "meta_piezas": 1700, "estado": "Activa", "piezas_entregadas": 0}])

def guardar_nueva_oc(orden, meta):
    try:
        supabase.table("Órdenes_Compra").insert({"orden_compra": orden, "meta_piezas": int(meta), "estado": "Activa", "piezas_entregadas": 0}).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar nueva OC: {e}")
        return False

def actualizar_oc_supabase(orden, meta, estado, entregadas):
    try:
        supabase.table("Órdenes_Compra").update({"meta_piezas": int(meta), "estado": estado, "piezas_entregadas": int(entregadas)}).eq("orden_compra", orden).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar la OC: {e}")
        return False

def registrar_entrega_piezas(orden, cantidad_entregada_nueva):
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
    try:
        supabase.table("Órdenes_Compra").delete().eq("orden_compra", orden).execute()
        supabase.table("Producción").delete().eq("orden_compra", orden).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar la OC: {e}")
        return False

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
    
    texto_cuerpo = f"Referente a su pedido <b><u>{oc_actual}</u></b> recibido el <b><u>{fecha_recibido_str}</u></b>. Se hace entrega de <b><u>{cantidad_piezas}</u></b> piezas de respaldo de silla <b><u>modelo Suiza</u></b>."
    style_cuerpo = ParagraphStyle('CuerpoRemision', fontName='Helvetica', fontSize=10.5, leading=16, textColor=colors.HexColor('#0F172A'))
    story.append(Paragraph(texto_cuerpo, style_cuerpo))
    story.append(Spacer(1, 260))
    
    style_firma_texto = ParagraphStyle('FirmaTexto', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#0F172A'), alignment=1)
    data_firmas = [
        [Paragraph("____________________________________________", style_normal), Paragraph