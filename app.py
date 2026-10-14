import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from supabase import create_client, Client
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración de la página con la identidad corporativa de Crealag
st.set_page_config(page_title="crealag - Control de Producción y Remisiones", layout="wide", page_icon="🏢")

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
    /* Estilo para los títulos de marca */
    .brand-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        color: #F8FAFC;
    }
    </style>
""", unsafe_allow_html=True)

# Conexión a Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
    db_status = True
except Exception as e:
    db_status = False

# --- NAVEGACIÓN EN LA BARRA LATERAL (SUPERIOR IZQUIERDA) ---
with st.sidebar:
    st.markdown("<h2 class='brand-title' style='color: #D4AF37; margin-bottom: 0px;'>crealag</h2>", unsafe_allow_html=True)
    st.caption("Fabricante mueblerio metalformado A.C. e INOX")
    st.markdown("---")
    
    # Selector en lista desplegable en la parte superior izquierda
    menu_seleccionado = st.selectbox(
        "Navegación del Sistema",
        ["📊 Producción y Registro", "📄 Generador de Remisiones"]
    )

# Título principal con branding integrado
st.markdown("<h1 class='brand-title'>crealag <span style='font-weight: 300; font-size: 24px; color: #94A3B8;'>| Control de Producción y Remisiones</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# --- SECCIÓN 1: REGISTRO DE PRODUCCIÓN ---
if menu_seleccionado == "📊 Producción y Registro":
    st.subheader("Panel de Control de Producción - Modelo Suiza")
    
    if db_status:
        st.success("Conexión con Supabase activa y operando correctamente.")
    else:
        st.warning("Verifica tus llaves de conexión a Supabase en la configuración de secrets.")

    with st.form("form_produccion"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fecha_prod = st.date_input("Fecha de Producción", datetime.now())
            operador = st.text_input("Operador / Taller", "")
            proceso = st.selectbox("Proceso", ["Corte", "Doblado", "Soldadura", "Pintura / Powder Coat", "Ensamble", "Empaque"])
        with col_p2:
            piezas_buenas = st.number_input("Piezas Fabricadas / Buenas", min_value=0, value=0, step=1)
            piezas_mermadas = st.number_input("Piezas Mermadas / Scrappeadas", min_value=0, value=0, step=1)
            observaciones_prod = st.text_area("Notas / Observaciones", "")

        guardar_prod = st.form_submit_button("💾 Guardar Registro de Producción")

    if guardar_prod:
        if db_status:
            try:
                datos = {
                    "fecha": fecha_prod.strftime("%Y-%m-%d"),
                    "operador": operador,
                    "proceso": proceso,
                    "cantidad": piezas_buenas,
                    "scraps": piezas_mermadas,
                    "observaciones": observaciones_prod
                }
                respuesta = supabase.table("produccion").insert(datos).execute()
                st.success("✅ ¡Registro de producción guardado con éxito en Supabase!")
            except Exception as err:
                st.error(f"Error al guardar los datos: {err}")
        else:
            st.error("No hay conexión a la base de datos.")

# --- SECCIÓN 2: GENERADOR DE REMISIONES ---
elif menu_seleccionado == "📄 Generador de Remisiones":
    st.subheader("Generador de Remisiones Oficiales")
    st.write("Rellena los datos para generar el documento oficial en PDF con el formato Crealag.")

    with st.form("form_remision"):
        col1, col2 = st.columns(2)
        with col1:
            atencion = st.text_input("Atención (Contacto)", "Ing. Laura Zamora")
            compania = st.text_input("Compañía / Cliente", "Herwong")
            puesto = st.text_input("Puesto", "Compras")
            email = st.text_input("Email", "compras.herwong@gmail.com")
            cel = st.text_input("Celular", "871-1442234")
            
        with col2:
            referencia = st.text_input("Referencia del Producto", "Respaldos sillas modelo Suiza")
            documento = st.text_input("Folio Documento", "HER-080526-REM")
            pedido_cliente = st.text_input("Referencia Cliente (Pedido)", "Pedido No. 01")
            fecha_remision = st.date_input("Fecha de Emisión", datetime.now())
            cantidad_piezas = st.number_input("Cantidad de Piezas", min_value=1, value=15)

        texto_pedido = st.text_area(
            "Texto Descriptivo del Pedido",
            f"Referente a su pedido recibido el {fecha_remision.strftime('%d/%m/%Y')}. Se hace entrega de {cantidad_piezas} piezas de respaldo de silla modelo Suiza."
        )

        submit_pdf = st.form_submit_button("Generar PDF de Remisión")

    if submit_pdf:
        def generar_pdf():
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            story = []
            
            styles = getSampleStyleSheet()
            style_normal = styles['Normal']
            
            style_titulo = ParagraphStyle('TituloCrealag', parent=style_normal, fontName='Helvetica-Bold', fontSize=26, textColor=colors.HexColor('#0A0F1D'))
            style_sub = ParagraphStyle('SubCrealag', parent=style_normal, fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#334155'))
            
            story.append(Paragraph("<b>crealag</b>", style_titulo))
            story.append(Paragraph("Fabricante mueblerio metalformado A.C. e INOX", style_sub))
            story.append(Spacer(1, 15))
            
            data_meta = [
                [Paragraph("<b>Atención:</b>", style_normal), Paragraph(atencion, style_normal), Paragraph("<b>Documento:</b>", style_normal), Paragraph(documento, style_normal)],
                [Paragraph("<b>Compañía:</b>", style_normal), Paragraph(compania, style_normal), Paragraph("<b>Referencia cliente:</b>", style_normal), Paragraph(pedido_cliente, style_normal)],
                [Paragraph("<b>Puesto:</b>", style_normal), Paragraph(puesto, style_normal), Paragraph("<b>Fecha:</b>", style_normal), Paragraph(fecha_remision.strftime('%d / %m / %Y'), style_normal)],
                [Paragraph("<b>Email:</b>", style_normal), Paragraph(email, style_normal), Paragraph("<b>Referencia:</b>", style_normal), Paragraph(referencia, style_normal)],
                [Paragraph("<b>Cel:</b>", style_normal), Paragraph(cel, style_normal), Paragraph("", style_normal), Paragraph("", style_normal)]
            ]
            
            t_meta = Table(data_meta, colWidths=[90, 200, 110, 140])
            t_meta.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(t_meta)
            story.append(Spacer(1, 20))
            
            style_cuerpo = ParagraphStyle('CuerpoRem', parent=style_normal, fontName='Helvetica', fontSize=11, leading=16, textColor=colors.HexColor('#0F172A'))
            story.append(Paragraph(texto_pedido, style_cuerpo))
            story.append(Spacer(1, 150))
            
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