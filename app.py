import streamlit as st
import time
import io
import os
from datetime import datetime
from utils.pdf_extractor import extract_text_from_pdf
from fpdf import FPDF
from database.db_manager import (registrar_usuario, login, obtener_documentos_por_rfp_y_usuario,
    guardar_rfp, eliminar_documento_usuario, guardar_documento_usuario, obtener_documento_usuario, obtener_todas_rfps_por_usuario,
    actualizar_documento_usuario, es_correo_valido, obtener_todos_documentos_por_usuario)
from utils.ai_client_gemini import (
    get_ai_summary_and_steps_gemini, get_ai_alignment_strategy_gemini, get_ai_competitive_advantage_gemini,
    get_ai_participation_decision_gemini, get_ai_detailed_understanding_gemini, get_ai_pain_points_gemini,
    get_ai_clarifying_questions_gemini, get_ai_resource_evaluation_gemini, get_ai_index_structure_gemini,
    get_ai_executive_summary_gemini, get_ai_proposed_solution_gemini, get_ai_value_added_gemini,
    get_ai_experience_credentials_gemini, get_ai_project_team_gemini, get_ai_timeline_budget_gemini,
    get_ai_requirements_compliance_gemini, generate_follow_up_steps_gemini
)

os.environ["WATCHDOG_OBSERVER"] = "false"

# Definir las categorías y subcategorías del menú
menu_options = {
    "Home": ["Mis RFPs"],
    "Carga y Configuración": ["Cargar RFP", "Configuración General"],
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
    st.session_state["current_category"] = "Home"
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Mis RFPs"
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
    st.session_state["current_category"] = "Home"
    st.session_state["current_page"] = "Mis RFPs"
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
            st.toast(f"Bienvenido, {st.session_state['user']['email']} 👋", icon="✅")
            st.session_state["show_welcome_message"] = False
    
    # Menú lateral
    with st.sidebar:
        st.sidebar.success(f"Usuario: {st.session_state['user']['email']}")
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

            user_id = st.session_state['user']['id']
            nombre_completo_archivos = ", ".join(file_names)

            rfp_id = guardar_rfp(nombre_completo_archivos, full_text.strip(), client_name, st.session_state["user"]["access_token"], st.session_state["user"]["id"], st.session_state['user']['refresh_token'])

            if rfp_id:
                st.session_state["rfp_id"] = rfp_id
                st.success("RFPs almacenadas correctamente.")
            else:
                st.error("Error al almacenar las RFPs.")
        elif uploaded_files and not client_name:
            st.warning("Por favor, introduce el nombre del cliente antes de continuar.")

    elif st.session_state["current_page"] == "Mis RFPs":
        st.subheader("📁 Mis RFPs")

        user_id = st.session_state['user']['id']

        if user_id:

            st.markdown("### Filtros de búsqueda")

            nombre_busqueda = st.text_input(
                "Buscar por nombre de archivo",
                value=st.session_state.get("filtro_nombre", "")
            )
            st.session_state["filtro_nombre"] = nombre_busqueda

            cliente_busqueda = st.text_input(
                "Buscar por cliente",
                value=st.session_state.get("filtro_cliente", "")
            )
            st.session_state["filtro_cliente"] = cliente_busqueda

            fecha_inicio = st.date_input(
                "Fecha de inicio",
                value=st.session_state.get("filtro_fecha_inicio", datetime.today())
            )
            st.session_state["filtro_fecha_inicio"] = fecha_inicio

            if st.button("🔄 Limpiar filtros"):
                st.session_state["filtro_nombre"] = ""
                st.session_state["filtro_cliente"] = ""
                st.session_state["filtro_fecha_inicio"] = datetime.today()
                st.session_state["rfps_visible"] = 5
                st.rerun()

        with st.spinner("⏳ Cargando tus RFPs..."):
            rfps = obtener_todas_rfps_por_usuario(user_id)
            rfps_con_docs = []

            for rfp in rfps:
                rfp_id = rfp["id"]
                usuario_id = rfp["user_id"]
                cliente = rfp["cliente"]
                nombre_archivo = rfp["nombre_archivo"]
                contenido = rfp["contenido"]
                fecha_subida = rfp["fecha_subida"]
                documentos = obtener_documentos_por_rfp_y_usuario(rfp_id, user_id)
                if documentos:
                    rfps_con_docs.append({
                        "id": rfp_id,
                        "user_id": usuario_id,
                        "cliente": cliente,
                        "nombre_archivo": nombre_archivo,
                        "contenido": contenido,
                        "fecha_subida": fecha_subida
                    })

            rfps_filtradas = []
            for rfp in rfps_con_docs:

                try:
                    fecha_obj = datetime.strptime(rfp["fecha_subida"], "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    try:
                        fecha_obj = datetime.strptime(rfp["fecha_subida"], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            fecha_obj = datetime.strptime(rfp["fecha_subida"], "%Y-%m-%d")
                        except ValueError:
                            fecha_obj = datetime.now()

                if (
                    (not nombre_busqueda or nombre_busqueda.lower() in rfp["nombre_archivo"].lower()) and
                    (not cliente_busqueda or cliente_busqueda.lower() in rfp["cliente"].lower())
                ):
                    rfp["fecha_obj"] = fecha_obj
                    rfps_filtradas.append(rfp)

        if rfps_filtradas:
            rfps_filtradas.sort(key=lambda x: x["fecha_obj"], reverse=True)

            if "rfps_visible" not in st.session_state:
                st.session_state["rfps_visible"] = 5

            rfps_a_mostrar = rfps_filtradas[:st.session_state["rfps_visible"]]

            headers = ["Nombre del archivo", "Cliente", "Fecha de subida", "Acciones"]
            
            # Estilo CSS para la tabla
            st.markdown("""
                <style>
                .table-container {
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                    font-size: 18px;
                    text-align: left;
                }
                .table-container th, .table-container td {
                    padding: 12px 15px;
                    border: 1px solid #ddd;
                }
                .table-container th {
                    background-color: #f2f2f2;
                    font-weight: bold;
                }
                .table-container tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                .table-container tr:hover {
                    background-color: #f1f1f1;
                }
                .table-container td button {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;
                }
                </style>
            """, unsafe_allow_html=True)

            # Crear la tabla
            st.markdown('<table class="table-container">', unsafe_allow_html=True)
            st.markdown('<tr>', unsafe_allow_html=True)
            for h in headers:
                st.markdown(f'<th>{h}</th>', unsafe_allow_html=True)
            st.markdown('</tr>', unsafe_allow_html=True)

            # Añadir las filas de datos
            for rfp in rfps_a_mostrar:
                st.markdown('<tr>', unsafe_allow_html=True)
                st.markdown(f'<td>{rfp["nombre_archivo"]}</td>', unsafe_allow_html=True)
                st.markdown(f'<td>{rfp["cliente"]}</td>', unsafe_allow_html=True)
                st.markdown(f'<td>{rfp["fecha_obj"].strftime("%d/%m/%Y %H:%M")}</td>', unsafe_allow_html=True)
                st.markdown(f'<td><button onclick="window.location.href=\'#\'">📄 Ver</button></td>', unsafe_allow_html=True)
                st.markdown('</tr>', unsafe_allow_html=True)

            st.markdown('</table>', unsafe_allow_html=True)


            if st.session_state["rfps_visible"] < len(rfps_filtradas):
                if st.button("⬇️ Mostrar más"):
                    st.session_state["rfps_visible"] += 5
                    st.rerun()
        else:
            st.info("No se encontraron RFPs que coincidan con los filtros.")
    
    elif st.session_state["current_page"] == "Detalle RFP":
        rfp_id = st.session_state.get("selected_rfp_id")
        user_id = st.session_state['user']['id']

        if rfp_id and user_id:
            if st.button("⬅️ Volver al listado"):
                st.session_state["current_page"] = "Mis RFPs"
                st.session_state.pop("selected_rfp_id", None)
                st.rerun()

            documentos = obtener_documentos_por_rfp_y_usuario(rfp_id, user_id)

            if not documentos:
                st.warning("Esta RFP no tiene documentos asociados.")
                st.stop()

            estructura_rfp = {
                "Evaluación Inicial": ["Análisis rápido", "Alineación estratégica", "Ventaja Competitiva", "Decisión de Participar"],
                "Análisis Profundo": ["Comprensión Detallada", "Identificación de 'dolores'", "Preguntas Aclaratorias", "Evaluación de Recursos"],
                "Desarrollo de la Propuesta": ["Estructura del Índice", "Resumen ejecutivo", "Solución Propuesta", "Beneficios y Valor Añadido", "Experiencia y Credenciales", "Equipo de Proyecto", "Cronograma y Presupuesto", "Cumplimiento de Requisitos"],
                "Revisión y Aprobación": ["Revisión Interna", "Aprobación Responsable"]
            }

            subcategorias_totales = [sub for lista in estructura_rfp.values() for sub in lista]

            if st.session_state["current_page"] in subcategorias_totales:
                subcategoria = st.session_state["current_page"]
                rfp_id = st.session_state.get("selected_rfp_id")
                user_id = st.session_state['user']['id']

                documento = obtener_documentos_por_rfp_y_usuario(rfp_id, user_id)

                if documento:
                    contenido_documento = documento[0]
                    if st.session_state["analysis_cache"].get(subcategoria) != contenido_documento:
                        st.session_state["analysis_cache"][subcategoria] = contenido_documento
                else:
                    if subcategoria in st.session_state["analysis_cache"]:
                        del st.session_state["analysis_cache"][subcategoria]

                if subcategoria in st.session_state["analysis_cache"]:
                    resumen_editable = st.text_area(
                        "Resumen Generado por IA",
                        st.session_state["analysis_cache"][subcategoria],
                        height=300
                    )
                else:
                    st.info("No hay resumen generado para esta subcategoría.")


            docs_por_categoria = {cat: {sub: [] for sub in subs} for cat, subs in estructura_rfp.items()}

            for doc in documentos:
                doc_id = doc["id"]
                titulo = doc["titulo"]
                contenido = doc["contenido"]
                fecha_creacion = doc["fecha_creacion"]
                nombre_categoria = doc["categorias"]["nombre"]
                nombre_subcategoria = doc["subcategorias"]["nombre"]
                
                if nombre_categoria in docs_por_categoria and nombre_subcategoria in docs_por_categoria[nombre_categoria]:
                    docs_por_categoria[nombre_categoria][nombre_subcategoria].append((titulo, contenido))

            categorias_con_docs = {
                cat: subs for cat, subs in docs_por_categoria.items()
                if any(sub_docs for sub_docs in subs.values())
            }

            if not categorias_con_docs:
                st.info("No hay contenido disponible en ninguna categoría.")
                st.stop()

            if "categoria_seleccionada" not in st.session_state:
                st.session_state["categoria_seleccionada"] = list(categorias_con_docs.keys())[0]

            if "subcategoria_seleccionada" not in st.session_state:
                primera_sub = list(categorias_con_docs[st.session_state["categoria_seleccionada"]].keys())[0]
                st.session_state["subcategoria_seleccionada"] = primera_sub

            # Estilos comunes para fondos claros u oscuros
            st.markdown("""
            <style>
                .titulo-seccion {
                    text-align: center;
                    font-size: 1.5rem;
                    font-weight: bold;
                    margin-top: 10px;
                    margin-bottom: 10px;
                    color: inherit;
                }
                .contenedor-ficha {
                    border: 1px solid rgba(0,0,0,0.2);
                    border-radius: 10px;
                    padding: 15px;
                    margin-top: 10px;
                    background-color: rgba(255, 255, 255, 0.05);
                }
                .contenedor-ficha.dark {
                    background-color: rgba(0, 0, 0, 0.3);
                }
            </style>
            """, unsafe_allow_html=True)

            # Categorías
            st.markdown('<div class="titulo-seccion">Categorías</div>', unsafe_allow_html=True)

            categoria_actual = st.session_state.get("categoria_seleccionada")

            if categoria_actual not in categorias_con_docs:
                categoria_actual = list(categorias_con_docs.keys())[0]
                st.session_state["categoria_seleccionada"] = categoria_actual

            cols = st.columns(len(categorias_con_docs))
            for i, categoria in enumerate(categorias_con_docs.keys()):
                estilo = "font-weight:bold; color:#ffffff; background-color:#4b6cb7; border-radius:5px; padding:5px 10px;" if categoria == st.session_state["categoria_seleccionada"] else "color:#4b6cb7;"
                with cols[i]:
                    if st.button(categoria, key=f"cat_{categoria}"):
                        categoria_actual = categoria
                        st.session_state["categoria_seleccionada"] = categoria_actual
                        subcats = categorias_con_docs[categoria]
                        primera_sub = next((s for s, d in subcats.items() if d), None)
                        st.session_state["subcategoria_seleccionada"] = primera_sub

            # Subcategorías
            subcategorias = {
                sub: docs for sub, docs in categorias_con_docs[categoria_actual].items() if docs
            }

            if st.session_state["subcategoria_seleccionada"] not in subcategorias:
                if subcategorias:
                    st.session_state["subcategoria_seleccionada"] = list(subcategorias.keys())[0]
                else:
                    st.info("No hay documentos en esta categoría.")
                    st.stop()

            st.markdown('<div class="titulo-seccion">Subcategorías</div>', unsafe_allow_html=True)
            cols_sub = st.columns(len(subcategorias))
            for i, subcat in enumerate(subcategorias.keys()):
                estilo = "font-weight:bold; color:#ffffff; background-color:#4b6cb7; border-radius:5px; padding:5px 10px;" if subcat == st.session_state["subcategoria_seleccionada"] else "color:#4b6cb7;"
                with cols_sub[i]:
                    if st.button(subcat, key=f"subcat_{subcat}"):
                        st.session_state["subcategoria_seleccionada"] = subcat


            docs = subcategorias[st.session_state["subcategoria_seleccionada"]]
            if docs:
                for doc in documentos:
                    doc_id = doc["id"]
                    titulo = doc["titulo"]
                    contenido = doc["contenido"]
                    fecha_creacion = doc["fecha_creacion"]
                    nombre_categoria = doc["categorias"]["nombre"]
                    nombre_subcategoria = doc["subcategorias"]["nombre"]

                    if (
                        nombre_categoria == st.session_state["categoria_seleccionada"]
                        and nombre_subcategoria == st.session_state["subcategoria_seleccionada"]
                    ):
                        with st.container(border=True):
                            
                            st.text_input("Título", value=titulo, key=f"titulo_{doc_id}")
                            st.text_area("Contenido", value=contenido, height=200, key=f"contenido_{doc_id}")
                            st.markdown(f"**Fecha de creación:** {fecha_creacion}")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("💾 Actualizar", key=f"actualizar_{doc_id}"):
                                    actualizar_documento_usuario(doc_id, st.session_state[f"titulo_{doc_id}"], st.session_state[f"contenido_{doc_id}"], user_id)
                                    st.session_state["analysis_cache"][nombre_subcategoria] = st.session_state[f"contenido_{doc_id}"]
                                    st.success("Documento actualizado correctamente.")
                                    st.rerun()
                            with col2:
                                if st.button("🗑️ Eliminar", key=f"eliminar_{doc_id}"):
                                    eliminar_documento_usuario(doc_id, user_id)
                                    st.session_state["analysis_cache"].pop(nombre_subcategoria, None)
                                    st.success("Documento eliminado correctamente.")
                                    st.rerun()
                            with col3:
                                pdf_buffer = generate_pdf(st.session_state[f"contenido_{doc_id}"]) 

                                st.download_button(
                                    label="Descargar como PDF",
                                    data=pdf_buffer.getvalue(),
                                    file_name=f"{st.session_state[f"titulo_{doc_id}"]} generado con IA.pdf",
                                    mime="application/pdf"
                                )

            else:
                st.info("No hay documentos en esta subcategoría.")

    
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
                    nombre_categoria = st.session_state["current_category"]
                    nombre_subcategoria = st.session_state["current_page"]
                    
                    if guardar_documento_usuario(rfp_id, titulo, resumen_editable, nombre_categoria, nombre_subcategoria):
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
        password = st.text_input("Contraseña", type="password")
        confirmar_password = st.text_input("Confirmar Contraseña", type="password")
        
        if st.button("Registrar"):
            if not email or not password or not confirmar_password:
                st.error("Todos los campos son obligatorios.")
            elif not es_correo_valido(email):
                st.error("El correo electrónico no es válido.")
            elif len(password) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            elif password != confirmar_password:
                st.error("Las contraseñas no coinciden.")
            elif registrar_usuario(email, password):
                st.success("Registro exitoso.")
                st.info("📧 Se ha enviado un correo de verificación. Por favor, revisa tu bandeja de entrada y confirma tu correo para poder iniciar sesión.")

            else:
                st.error("Error al registrar el usuario. Inténtalo de nuevo más tarde.")

    elif menu == "Inicio de Sesión":
        st.subheader("Inicio de Sesión")
        email = st.text_input("Correo Electrónico")
        password = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            response = login(email, password)
            if response:
                st.session_state["logged_in"] = True
                st.session_state["user"] = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                }
                st.rerun()
            else:
                st.error("Correo electrónico o contraseña incorrectos.")