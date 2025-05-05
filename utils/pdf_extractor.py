from PyPDF2 import PdfReader
from fpdf import FPDF
import os
import streamlit as st
import io

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()

    logo_path = "BID_AI_Logotype_Light.jpeg"

    if os.path.exists(logo_path):
        try:
            logo_width = 50
            page_width = pdf.w
            x_position = (page_width - logo_width) / 2
            pdf.image(logo_path, x=x_position, y=10, w=logo_width)
            pdf.ln(50)
        except RuntimeError as e:
            st.error(f"⚠️ Error al insertar el logo en el PDF: {e}")
    else:
        st.warning(f"⚠️ Logo no encontrado en: {logo_path}")

    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(0, 10, "Análisis Automático de RFP", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    content = clean_text(content)
    pdf.multi_cell(0, 10, content)

    pdf_buffer = io.BytesIO()
    pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
    pdf_buffer.write(pdf_output)
    pdf_buffer.seek(0)
    return pdf_buffer

def clean_text(text):
    return ''.join(c if ord(c) < 256 else '?' for c in text)