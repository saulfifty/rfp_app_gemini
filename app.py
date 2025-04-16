import streamlit as st
import time
import io
import streamlit.components.v1 as components
from datetime import datetime
from utils.pdf_extractor import extract_text_from_pdf
from fpdf import FPDF
from database.db_manager import (inicializar_base_de_datos, get_connection, registrar_usuario, verificar_credenciales, 
    guardar_rfp, guardar_respuesta_ia, guardar_documento_usuario, obtener_documento_usuario, 
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
    "Carga y Configuración": ["Cargar RFP", "Configuración General", "Mis Documentos"],
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

        for category in menu_options:
            is_active = st.session_state["current_category"] == category
            button_label = f"▶ {category}" if is_active else category
            if st.button(button_label, key=f"btn_{category}"):
                st.session_state["current_category"] = category
                st.session_state["current_page"] = menu_options[category][0]

    components.html("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" integrity="sha512-jQMnUe1tbvLIszv1qKmAg5qJOC9IxA1I3szTgEDUaz4BxTrjw5mwoq+TQQHzlRVmL0D5JApztEt9M2rFu/Un4g==" crossorigin="anonymous" referrerpolicy="no-referrer" />

    <style>
    /* Tipografía corporativa */
    html, body, div, p, button {
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        color: #1f2937; /* gris oscuro corporativo */
    }

    /* Fondo sobrio */
    body {
        background-color: #f4f6f8;
    }

    /* Botones del menú lateral */
    section[data-testid="stSidebar"] button {
        background-color: transparent !important;
        color: #374151 !important;
        font-weight: 500;
        border: none;
        border-left: 5px solid transparent;
        transition: all 0.3s ease-in-out;
        text-align: left;
        padding-left: 15px;
        margin-bottom: 5px;
    }

    section[data-testid="stSidebar"] button:hover {
        background-color: #e5e7eb !important;
        border-left: 5px solid #0ea5e9;
        color: #0ea5e9 !important;
        transform: translateX(3px);
    }

    /* Categoría activa */
    section[data-testid="stSidebar"] button:focus:not(:active) {
        background-color: #e0f2fe !important;
        color: #0284c7 !important;
        border-left: 5px solid #0284c7;
    }

    /* Subcategorías */
    button[kind="secondary"] {
        background-color: #ffffff;
        color: #1f2937;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        font-size: 14px;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    button[kind="secondary"]:hover {
        background-color: #f1f5f9;
        color: #0f172a;
        border-color: #0ea5e9;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Animaciones suaves para cambio de sección */
    h1, h2, h3, .stMarkdown {
        animation: fadeSlideIn 0.6s ease-in-out;
    }

    @keyframes fadeSlideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
    }

    /* Toast de bienvenida */
    [data-testid="stToast"] {
        font-weight: 600;
        background-color: #f0f9ff !important;
        color: #0369a1 !important;
    }

    /* Íconos SVG */
    .fa {
        margin-right: 8px;
    }
                    
    .active-category {
        background-color: #e0f2fe !important;
        color: #0284c7 !important;
        border-left: 5px solid #0284c7 !important;
    }
    </style>
    """, height=0)

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
        with col:
            st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)
            if st.button(subcategory, key=subcategory, use_container_width=True, help=subcategory):
                st.session_state["current_page"] = subcategory

    # Resaltar la página actual
    st.markdown(f"**Página actual:** {st.session_state['current_page']}")
    
    # Contenido de la página actual
    if st.session_state["current_page"] == "Cargar RFP":
        st.subheader("Subir y Analizar RFP")
        uploaded_file = st.file_uploader("Sube un archivo RFP", type="pdf")
        
        if uploaded_file is not None:
            with open("uploaded.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            text = extract_text_from_pdf("uploaded.pdf")
            st.session_state["rfp_text"] = text
            st.text_area("Contenido del RFP", text, height=200)
            user_id = obtener_user_id_por_email(st.session_state["user"])
            rfp_id = guardar_rfp(user_id, uploaded_file.name, text)
            if rfp_id:
                st.session_state["rfp_id"] = rfp_id
                st.success("RFP almacenada correctamente.")
            else:
                st.error("Error al almacenar la RFP.")

    elif st.session_state["current_page"] == "Mis Documentos":
        st.subheader("📁 Mis Documentos")

        user_id = obtener_user_id_por_email(st.session_state["user"])

        if user_id:
            # Crear campos de búsqueda para el título y la fecha
            titulo_busqueda = st.text_input("Buscar por título de RFP", "")
            fecha_inicio = st.date_input("Fecha de inicio", min_value=datetime(2000, 1, 1).date())
            fecha_fin = st.date_input("Fecha de fin", max_value=datetime.today().date())

            # Obtener todos los documentos del usuario
            documentos = obtener_todos_documentos_por_usuario(user_id)

            if documentos:
                # Filtrar documentos según los criterios de búsqueda
                documentos_filtrados = []
                for doc in documentos:
                    doc_id, rfp_id, titulo, contenido, fecha_creacion = doc

                    # Convertir la fecha_creacion a un objeto de fecha para compararla
                    fecha_creacion_obj = datetime.strptime(fecha_creacion, "%Y-%m-%d %H:%M:%S").date()

                    # Verificar si el título y la fecha cumplen con los filtros
                    if (titulo_busqueda.lower() in titulo.lower() and 
                        fecha_inicio <= fecha_creacion_obj <= fecha_fin):
                        documentos_filtrados.append(doc)

                # Mostrar los documentos filtrados
                if documentos_filtrados:
                    for doc in documentos_filtrados:
                        doc_id, rfp_id, titulo, contenido, fecha_creacion = doc

                        with st.expander(f"{titulo} (Creado el {fecha_creacion})"):
                            nuevo_titulo = st.text_input(f"Título para doc ID {doc_id}", value=titulo, key=f"titulo_{doc_id}")
                            nuevo_contenido = st.text_area(f"Contenido para doc ID {doc_id}", value=contenido, height=200, key=f"contenido_{doc_id}")
                            if st.button("Actualizar", key=f"btn_actualizar_{doc_id}"):
                                success = actualizar_documento_usuario(doc_id, nuevo_titulo, nuevo_contenido, user_id)
                                if success:
                                    st.success("Documento actualizado correctamente.")
                                    st.rerun()
                                else:
                                    st.error("Hubo un error al actualizar el documento.")
                else:
                    st.info("No se encontraron documentos que coincidan con los filtros.")
            else:
                st.info("No tienes documentos almacenados aún.")
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