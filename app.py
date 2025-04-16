import streamlit as st
import time
import io
import os
from datetime import datetime
from utils.pdf_extractor import extract_text_from_pdf
from fpdf import FPDF
from database.db_manager import (inicializar_base_de_datos, registrar_usuario, verificar_credenciales, 
    guardar_rfp, guardar_respuesta_ia, guardar_documento_usuario, obtener_documento_usuario, obtener_todas_rfps_por_usuario,
    actualizar_documento_usuario, obtener_user_id_por_email, es_correo_valido, obtener_todos_documentos_por_usuario)
from utils.ai_client_gemini import (
    get_ai_summary_and_steps_gemini, get_ai_alignment_strategy_gemini, get_ai_competitive_advantage_gemini,
    get_ai_participation_decision_gemini, get_ai_detailed_understanding_gemini, get_ai_pain_points_gemini,
    get_ai_clarifying_questions_gemini, get_ai_resource_evaluation_gemini, get_ai_index_structure_gemini,
    get_ai_executive_summary_gemini, get_ai_proposed_solution_gemini, get_ai_value_added_gemini,
    get_ai_experience_credentials_gemini, get_ai_project_team_gemini, get_ai_timeline_budget_gemini,
    get_ai_requirements_compliance_gemini, generate_follow_up_steps_gemini
)

# Inicializar la base de datos
inicializar_base_de_datos()

# Definir las categorías y subcategorías del menú
menu_options = {
    "Carga y Configuración": ["Cargar RFP", "Configuración General", "Mis RFPs"],
    "Evaluación Inicial": ["Análisis rápido", "Alineación estratégica", "Ventaja Competitiva", "Decisión de Participar"],
    "Análisis Profundo": ["Comprensión Detallada", "Identificación de 'dolores'", "Preguntas Aclaratorias", "Evaluación de Recursos"],
    "Desarrollo de la Propuesta": ["Estructura del Índice", "Resumen ejecutivo", "Solución Propuesta", "Beneficios y Valor Añadido", "Experiencia y Credenciales", "Equipo de Proyecto", "Cronograma y Presupuesto", "Cumplimiento de Requisitos"],
    "Revisión y Aprobación": ["Revisión Interna", "Aprobación Responsable"]
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "current_category" not in st.session_state:
    st.session_state["current_category"] = "Carga y Configuración"
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Cargar RFP"
if "rfp_text" not in st.session_state:
    st.session_state["rfp_text"] = ""
if "show_steps_button" not in st.session_state:
    st.session_state["show_steps_button"] = False
if "analysis_cache" not in st.session_state:
    st.session_state["analysis_cache"] = {}
if "respuesta_guardada" not in st.session_state:
    st.session_state["respuesta_guardada"] = False
if "show_welcome_message" not in st.session_state:
    st.session_state["show_welcome_message"] = True
if "follow_up_steps" not in st.session_state:
    st.session_state["follow_up_steps"] = {}

# Función para cerrar sesión
def logout():
    st.session_state["logged_in"] = False
    st.session_state["user"] = None
    st.session_state["current_category"] = "Carga y Configuración"
    st.session_state["current_page"] = "Cargar RFP"
    st.session_state["show_welcome_message"] = True

def clean_text(text):
    return ''.join(c if ord(c) < 256 else '?' for c in text)

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

# Función para restablecer análisis al cambiar de categoría o subcategoría
def reset_analysis():
    current_page = st.session_state.get("current_page", "")
    if current_page and "analysis" in st.session_state:
        st.session_state["analysis_cache"][current_page] = ""

# Layout principal
if st.session_state["logged_in"]:
    col1, col2 = st.columns([1, 8])
    with col1:
        if st.get_option("theme.base") == "dark":
            st.image("BID_AI_Logotype_dark.png", use_container_width=True)
        else:
            st.image("BID_AI_Logotype_Light.jpeg", use_container_width=True)
    with col2:
        st.title("Análisis de RFPs con IA")
        if st.session_state["show_welcome_message"]:
            st.toast(f"Bienvenido, {st.session_state['user']} 👋", icon="✅")
            st.session_state["show_welcome_message"] = False
    
    # Menú lateral
    with st.sidebar:
        st.sidebar.success(f"Usuario: {st.session_state['user']}")

        for category in menu_options.keys():
            if st.button(category):
                st.session_state["current_category"] = category
                st.session_state["current_page"] = menu_options[category][0]
        st.button("Cerrar Sesión", on_click=logout)

    # CSS para uniformizar el tamaño de los botones del submenú y el botón de descarga
    st.markdown("""
        <style>
        .stButton button, .stDownloadButton button {
            height: 60px;
            width: 100%;
            margin: 5px 0;
            font-size: 16px;
            background-color: var(--primary-color);
            color: var(--text-color);
            border: 1px solid var(--secondary-background-color);
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        .stButton button:hover, .stDownloadButton button:hover {
            filter: brightness(0.95);
            border-color: var(--text-color);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Submenú con cajitas
    st.subheader(f"{st.session_state['current_category']}")
    sub_categories = menu_options[st.session_state["current_category"]]
    col1, col2, col3, col4 = st.columns(4)
    for i, subcategory in enumerate(sub_categories):
        col = [col1, col2, col3, col4][i % 4]
        if col.button(subcategory, key=subcategory):
            st.session_state["current_page"] = subcategory

    # Resaltar la página actual
    st.markdown(f"**Página actual:** {st.session_state['current_page']}")
    
    # Contenido de la página actual
    if st.session_state["current_page"] == "Cargar RFP":
        st.subheader("Subir y Analizar RFP")
        
        client_name = st.text_input("Nombre del cliente")

        uploaded_files = st.file_uploader(
            "Sube uno o varios archivos PDF de la RFP",
            type="pdf",
            accept_multiple_files=True
        )

        if uploaded_files and client_name:
            full_text = ""
            file_names = []

            for uploaded_file in uploaded_files:
                file_path = f"temp_{uploaded_file.name}"
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                extracted_text = extract_text_from_pdf(file_path)
                full_text += f"\n\n--- Contenido de {uploaded_file.name} ---\n\n{extracted_text}"
                file_names.append(uploaded_file.name)

            st.text_area("Contenido combinado de los RFPs", full_text.strip(), height=300)
            st.session_state["rfp_text"] = full_text.strip()

            user_id = obtener_user_id_por_email(st.session_state["user"])
            nombre_completo_archivos = ", ".join(file_names)

            rfp_id = guardar_rfp(user_id, nombre_completo_archivos, full_text.strip(), client_name)

            if rfp_id:
                st.session_state["rfp_id"] = rfp_id
                st.success("RFPs almacenadas correctamente.")
            else:
                st.error("Error al almacenar las RFPs.")
        elif uploaded_files and not client_name:
            st.warning("Por favor, introduce el nombre del cliente antes de continuar.")

    elif st.session_state["current_page"] == "Mis RFPs":
        st.subheader("📁 Mis RFPs")

        user_id = obtener_user_id_por_email(st.session_state["user"])

        if user_id:

            st.markdown("### Filtros de búsqueda")

            nombre_busqueda = st.text_input("Buscar por nombre de archivo")
            cliente_busqueda = st.text_input("Buscar por cliente")
            fecha_inicio = st.date_input("Fecha de inicio", value=datetime(2000, 1, 1).date())

            rfps = obtener_todas_rfps_por_usuario(user_id)

            rfps_filtradas = []
        for rfp in rfps:
            rfp_id, usuario_id, cliente, nombre_archivo, contenido, fecha_subida = rfp

            # Convertir fecha_subida a objeto datetime
            try:
                fecha_obj = datetime.strptime(fecha_subida, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                try:
                    fecha_obj = datetime.strptime(fecha_subida, "%Y-%m-%d").date()
                except ValueError:
                    fecha_obj = None

            if (
                (not nombre_busqueda or nombre_busqueda.lower() in nombre_archivo.lower()) and
                (not cliente_busqueda or cliente_busqueda.lower() in cliente.lower())
            ):
                rfps_filtradas.append(rfp)

        if rfps_filtradas:
            for rfp in rfps_filtradas:
                rfp_id, usuario_id, cliente, nombre_archivo, contenido, fecha_subida = rfp
                with st.expander(f"📄 {nombre_archivo} - Cliente: {cliente} - Subida: {fecha_subida}"):
                    st.markdown(f"**Contenido:**")
                    st.write(contenido)
        else:
            st.info("No se encontraron RFPs que coincidan con los filtros.")
    else:
        st.error("No se pudo encontrar el usuario en la base de datos.")

    
    function_mapping = {
        "Análisis rápido": get_ai_summary_and_steps_gemini,
        "Alineación estratégica": get_ai_alignment_strategy_gemini,
        "Ventaja Competitiva": get_ai_competitive_advantage_gemini,
        "Decisión de Participar": get_ai_participation_decision_gemini,
        "Comprensión Detallada": get_ai_detailed_understanding_gemini,
        "Identificación de 'dolores'": get_ai_pain_points_gemini,
        "Preguntas Aclaratorias": get_ai_clarifying_questions_gemini,
        "Evaluación de Recursos": get_ai_resource_evaluation_gemini,
        "Estructura del Índice": get_ai_index_structure_gemini,
        "Resumen ejecutivo": get_ai_executive_summary_gemini,
        "Solución Propuesta": get_ai_proposed_solution_gemini,
        "Beneficios y Valor Añadido": get_ai_value_added_gemini,
        "Experiencia y Credenciales": get_ai_experience_credentials_gemini,
        "Equipo de Proyecto": get_ai_project_team_gemini,
        "Cronograma y Presupuesto": get_ai_timeline_budget_gemini,
        "Cumplimiento de Requisitos": get_ai_requirements_compliance_gemini,
    }

    reset_analysis()
    
    # Dentro de la parte donde generas el resumen con IA
    current_page = st.session_state.get("current_page", "")
    if current_page in function_mapping:
        st.subheader(current_page)
        st.text_area("Contenido extraído de la RFP", st.session_state["rfp_text"], height=200)

        button_text = f"Generar {current_page} con IA"
        if st.button(button_text):
            if st.session_state["rfp_text"]:

                with st.spinner("⏳ Generando respuesta con IA..."):

                    analysis, steps = function_mapping[current_page](st.session_state["rfp_text"])
                    st.session_state["analysis_cache"][current_page] = analysis
                    st.session_state["follow_up_steps"][current_page] = steps
                    st.session_state["show_steps_button"] = True

        # Mostrar análisis si existe para la categoría actual
        if "analysis_cache" in st.session_state and st.session_state.get("current_page", "") in st.session_state["analysis_cache"]:
            resumen_editable = st.text_area("Resumen Generado por IA", st.session_state["analysis_cache"][st.session_state["current_page"]], height=300)
            
            if resumen_editable != st.session_state["analysis_cache"][st.session_state["current_page"]]:
                st.session_state["analysis_cache"][st.session_state["current_page"]] = resumen_editable

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Guardar en la Base de Datos"):
                    rfp_id = st.session_state.get("rfp_id", None)
                    titulo = f"{current_page} generado con IA"
                    pasos_sugeridos = generate_follow_up_steps_gemini(st.session_state["rfp_text"], "Análisis")
                    
                    if guardar_documento_usuario(rfp_id, titulo, resumen_editable):
                        st.session_state["respuesta_guardada"] = True
                        st.session_state["analysis_cache"][current_page] = resumen_editable
                    else:
                        st.error("Error al guardar la respuesta en la base de datos.")

            if st.session_state.get("respuesta_guardada"):
                success_message = st.empty()
                success_message.success("Respuesta guardada correctamente en la base de datos.")
                time.sleep(3)
                success_message.empty()
                st.session_state["respuesta_guardada"] = False

            with col2:
                pdf_buffer = generate_pdf(resumen_editable) 

                st.download_button(
                    label="Descargar como PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"{current_page} generado con IA.pdf",
                    mime="application/pdf"
                )
        
        # Para restaurar la respuesta modificada cuando el usuario vuelve a la categoría:
        if current_page in st.session_state["analysis_cache"] and st.session_state["analysis_cache"][current_page]:
            # Ya está almacenada una respuesta modificada previamente
            respuesta_modificada = st.session_state["analysis_cache"][current_page]
        else:
            respuesta_modificada = ""

        if current_page in st.session_state["analysis_cache"] and st.session_state["analysis_cache"][current_page]:
            if st.button("Generar pasos con IA"):
                steps = generate_follow_up_steps_gemini(st.session_state["rfp_text"], "Análisis")
                st.write("### Pasos Sugeridos")
                st.write(steps)

else:
    menu = st.sidebar.selectbox("Menú", ["Inicio de Sesión", "Registro"])
    if menu == "Registro":
        st.subheader("Registro de Usuario")

        email = st.text_input("Correo Electrónico")
        username = st.text_input("Nombre de Usuario")
        password = st.text_input("Contraseña", type="password")
        confirmar_password = st.text_input("Confirmar Contraseña", type="password")
        
        if st.button("Registrar"):
            if not email or not username or not password or not confirmar_password:
                st.error("Todos los campos son obligatorios.")
            elif not es_correo_valido(email):
                st.error("El correo electrónico no es válido.")
            elif password != confirmar_password:
                st.error("Las contraseñas no coinciden.")
            elif verificar_credenciales(username, password):
                st.error("El nombre de usuario ya existe.")
            else:
                registrar_usuario(username, email, password)
                st.success("Usuario registrado correctamente.")

    elif menu == "Inicio de Sesión":
        st.subheader("Inicio de Sesión")
        email = st.text_input("Correo Electrónico")
        password = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            if verificar_credenciales(email, password):
                st.session_state["logged_in"] = True
                st.session_state["user"] = email
                st.rerun()
            else:
                st.error("Correo electrónico o contraseña incorrectos.")