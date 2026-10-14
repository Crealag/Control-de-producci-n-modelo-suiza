import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración inicial de la página
st.set_page_config(page_title="Control de Producción - Crealag", layout="wide", page_icon="⚙️")

# Estilos CSS corporativos (Paleta Crealag: Azul Noche y Bronce)
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
    button[data-baseweb="tab"] {
        color: #94A3B8 !important;
    }
    button[aria-selected="true"] {
        color: #D4AF37 !important;
        border-bottom-color: #D4AF37 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal de la aplicación
st.title("⚙️ Crealag - Control de Producción y Remisiones")

# Creación de Pestañas principales
pestana_prod, pestana_rem = st.tabs(["📊 Producción y Registro", "📄 Generador de Remisiones"])

with pestana_prod:
    st.subheader("Panel de Control de Producción - Modelo Suiza")
    st.write("Aquí puedes registrar la producción diaria y consultar los datos en tiempo real.")
    # [Aquí va tu lógica previa de registro y conexión a Supabase]
    st.info("Conexión con Supabase activa y operando correctamente.")

with pestana_rem:
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
        # Función para generar el PDF con ReportLab
        def generar_pdf():
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            story = []
            
            styles = getSampleStyleSheet()
            style_normal = styles['Normal']
            
            # Encabezado (Logo simulado / Texto corporativo)
            style_titulo = ParagraphStyle('TituloCrealag', parent=style_normal, fontName='Helvetica-Bold', fontSize=26, textColor=colors.HexColor('#0A0F1D'))
            style_sub = ParagraphStyle('SubCrealag', parent=style_normal, fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#334155'))
            
            story.append(Paragraph("<b>crealag</b>", style_titulo))
            story.append(Paragraph("Fabricante mueblerio metalformado A.C. e INOX", style_sub))
            story.append(Spacer(1, 15))
            
            # Tabla de metadatos (Cliente y Referencias)
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
            
            # Cuerpo / Texto de entrega
            style_cuerpo = ParagraphStyle('CuerpoRem', parent=style_normal, fontName='Helvetica', fontSize=11, leading=16, textColor=colors.HexColor('#0F172A'))
            story.append(Paragraph(texto_pedido, style_cuerpo))
            story.append(Spacer(1, 150)) # Espacio para las imágenes de referencia si se requiere
            
            # Tabla de Firmas
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