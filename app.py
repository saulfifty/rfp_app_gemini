import streamlit as st
from utils.pdf_extractor import extract_text_from_pdf
from utils.ai_client import get_ai_summary_and_steps
from database.db_manager import init_db

init_db()

st.title("Análisis de RFPs con IA")

uploaded_file = st.file_uploader("Sube un archivo RFP", type="pdf")

if uploaded_file is not None:
    with open("uploaded.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    text = extract_text_from_pdf("uploaded.pdf")
    st.text_area("Contenido del RFP", text, height=200)

    if st.button("Analizar con IA"):
        summary = get_ai_summary_and_steps(text)
        st.subheader("Resumen")
        st.write(summary)