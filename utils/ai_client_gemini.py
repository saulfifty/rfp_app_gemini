import requests
import streamlit as st
from mdclense.parser import MarkdownParser

GEMINI_API_KEY = st.secrets["GEMINI"]["API_KEY"]

def analyze_rfp_gemini(rfp_text, category, prompt, language="español"):
    print(f"Generando análisis para {category}...")
    try:
        chunk_size = 1024
        chunks = [rfp_text[i:i+chunk_size] for i in range(0, len(rfp_text), chunk_size)]

        summary_text = ""
        for chunk in chunks:
            if not chunk.strip():
                continue

            input_length = len(chunk.split())
            max_len = min(800, int(input_length * 0.8))
            min_len = max(50, int(input_length * 0.3))

            if min_len >= max_len:
                min_len = max(50, int(max_len * 0.5))

            try:
                
                if not GEMINI_API_KEY:
                    raise ValueError("La clave API de Gemini no está definida en las variables de entorno.")

                url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}'
                headers = {'Content-Type': 'application/json'}
                data = {
                    "contents": [
                        {
                            "parts": [
                                {"text": f"{category}: {chunk}\n\n{prompt}\n\nResponde en {language} de forma clara y profesional."}
                            ]
                        }
                    ]
                }

                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    response_data = response.json()

                    if response_data and 'candidates' in response_data:
                        summary_text += response_data['candidates'][0]['content']['parts'][0]['text'] + " "
                    else:
                        print(f"Respuesta sin texto: {response_data}")
                else:
                    print(f"Error en la solicitud HTTP: {response.status_code} - {response.text}")

            except Exception as inner_e:
                print(f"Error generando el resumen para un fragmento: {inner_e}")

        analysis = f"{category}: {summary_text.strip()}"
        suggested_steps = generate_follow_up_steps_gemini(summary_text, category)

        formatted_analysis = clean_gemini_response(analysis)

        formatted_steps = clean_gemini_response(suggested_steps)

        return formatted_analysis, formatted_steps
    except Exception as e:
        print(f"Error al procesar el análisis para {category}: {e}")
        return f"Error: {e}", ""

def generate_follow_up_steps_gemini(summary_text, category):
    prompts = {
        "Análisis Rápido": "Proporciona un análisis completo de los puntos clave y los pasos necesarios para abordarlos.",
        "Alineación Estratégica": "Evalúa la alineación estratégica y sugiere pasos para mejorar el ajuste.",
        "Ventaja Competitiva": "Identifica ventajas competitivas clave y proporciona pasos para maximizar su impacto.",
        "Decisión de Participación": "Evalúa la viabilidad de participar y propone pasos concretos para preparar la propuesta.",
        "Entendimiento Detallado": "Desglosa los requisitos y sugiere pasos para cumplirlos eficientemente.",
        "Identificación de Problemas": "Identifica los desafíos y problemas clave y propone estrategias para abordarlos.",
        "Preguntas de Clarificación": "Genera preguntas aclaratorias sobre los requisitos y expectativas del cliente.",
        "Evaluación de Recursos": "Identifica recursos necesarios y sugiere estrategias para gestionarlos.",
        "Estructura del Índice": "Proporciona una estructura clara y organizada para la respuesta a la RFP.",
        "Resumen Ejecutivo": "Redacta un resumen que destaque los puntos clave y beneficios para el cliente.",
        "Solución Propuesta": "Describe cómo la solución aborda los requisitos del cliente y aporta valor.",
        "Valor Añadido": "Explica los beneficios específicos y ventajas competitivas de la propuesta.",
        "Experiencia y Credenciales": "Resume la experiencia relevante en proyectos similares y logros clave.",
        "Equipo de Proyecto": "Presenta el equipo con roles y responsabilidades relevantes.",
        "Cronograma y Presupuesto": "Proporciona un cronograma detallado y estimación de presupuesto.",
        "Cumplimiento de Requisitos": "Valida el cumplimiento de requisitos y sugiere áreas de ajuste.",
        "Casos de Uso": "Genera ejemplos de casos de uso relevantes para la propuesta."
    }
    prompt = prompts.get(category, "Genera pasos claros y accionables.")
    gemini_prompt = f"{prompt}\n\nResumen del análisis:\n{summary_text.strip()}\n\nPasos sugeridos para abordar los puntos clave mencionados en el análisis:"
    return gemini_prompt

def clean_gemini_response(text):

    if isinstance(text, (tuple, list)):
        text = text[0]
    parser = MarkdownParser()
    return parser.parse(text).strip()

def get_ai_summary_and_steps_gemini(rfp_text, category="Análisis Rápido"):
    prompt = "Como experto en análisis de RFP, proporciona un resumen completo y profesional del siguiente documento. Resume los objetivos principales, el alcance y los requisitos clave. Luego, enumera los pasos sugeridos para abordar cada punto importante."
    return analyze_rfp_gemini(rfp_text, category, prompt)

def get_ai_alignment_strategy_gemini(rfp_text, category="Alineación Estratégica"):
    prompt = (
        "Como experto en análisis estratégico, evalúa la alineación del proyecto descrito en la RFP con la experiencia de la empresa. "
        "Destaca fortalezas y debilidades potenciales, y proporciona pasos claros para mejorar el ajuste estratégico. "
        "Responde en español de forma clara y profesional."
    )
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_competitive_advantage_gemini(rfp_text, category="Ventaja Competitiva"):
    prompt = "Como experto en análisis competitivo, identifica los diferenciadores clave y ventajas que la empresa puede aprovechar frente a los competidores. Proporciona un desglose de fortalezas y áreas de mejora, seguido de pasos accionables."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_participation_decision_gemini(rfp_text, category="Decisión de Participación"):
    prompt = "Como experto en análisis de decisiones, evalúa la viabilidad de participar en la RFP en función de los recursos y capacidades actuales. Proporciona una recomendación clara y los pasos necesarios para preparar una propuesta competitiva."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_detailed_understanding_gemini(rfp_text, category="Entendimiento Detallado"):
    prompt = "Como experto en análisis de RFP, desglosa los requisitos clave y las expectativas del cliente. Identifica restricciones y criterios de éxito."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_pain_points_gemini(rfp_text, category="Identificación de Problemas"):
    prompt = "Como experto en análisis de problemas, identifica los desafíos y problemas que el cliente busca resolver en la RFP. Sugiere estrategias efectivas para abordar estos problemas."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_clarifying_questions_gemini(rfp_text, category="Preguntas de Clarificación"):
    prompt = "Como experto en análisis de requisitos, genera una lista de preguntas aclaratorias basadas en los requisitos y expectativas del cliente mencionados en la RFP. Asegúrate de que las preguntas sean relevantes y específicas."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_resource_evaluation_gemini(rfp_text, category="Evaluación de Recursos"):
    prompt = ("Como experto en evaluación de recursos, identifica los recursos necesarios para abordar la RFP, "
          "incluyendo personal, tecnología y presupuesto. Evalúa la disponibilidad de recursos y los posibles desafíos. "
          "Responde en español de manera clara y concisa.")
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_index_structure_gemini(rfp_text, category="Estructura del Índice"):
    prompt = "Como experto en redacción de propuestas, genera una estructura de índice para la respuesta a la RFP, incluyendo secciones clave como introducción, solución propuesta, experiencia previa, cronograma y presupuesto."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_executive_summary_gemini(rfp_text, category="Resumen Ejecutivo"):
    prompt = "Como experto en redacción ejecutiva, redacta un resumen que destaque los puntos clave de la propuesta, incluyendo objetivos, solución ofrecida y principales beneficios para el cliente."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_proposed_solution_gemini(rfp_text, category="Solución Propuesta"):
    prompt = "Como experto en soluciones propuestas, describe cómo la solución propuesta aborda los requisitos del cliente, enfatizando el valor añadido y los beneficios específicos."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_value_added_gemini(rfp_text, category="Valor Añadido"):
    prompt = "Como experto en análisis de valor añadido, explica de manera clara y convincente los beneficios específicos que aporta la solución propuesta, destacando ventajas competitivas."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_experience_credentials_gemini(rfp_text, category="Experiencia y Credenciales"):
    prompt = "Como experto en credenciales y experiencia, resume la experiencia relevante de la empresa en proyectos similares, destacando logros clave y referencias significativas."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_project_team_gemini(rfp_text, category="Equipo de Proyecto"):
    prompt = "Como experto en gestión de proyectos, presenta el equipo de proyecto, incluyendo roles, responsabilidades y experiencia relevante de cada miembro."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_timeline_budget_gemini(rfp_text, category="Cronograma y Presupuesto"):
    prompt = "Como experto en planificación y presupuestación, proporciona un cronograma detallado con fechas clave y una estimación clara del presupuesto, considerando recursos y fases del proyecto."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_requirements_compliance_gemini(rfp_text, category="Cumplimiento de Requisitos"):
    prompt = "Como experto en cumplimiento de requisitos, valida si la propuesta cumple con todos los requisitos descritos en la RFP. Indica posibles brechas o áreas que requieran ajustes o aclaraciones."
    return analyze_rfp_gemini(rfp_text, category, prompt)


def get_ai_use_cases_gemini(rfp_text, category="Casos de Uso"):
    prompt = ("Como experto en análisis de casos de uso, identifica posibles escenarios prácticos en los que la solución propuesta "
                "pueda ser aplicada para satisfacer los requisitos del cliente. Proporciona ejemplos claros y detallados que demuestren "
                "el valor y la efectividad de la solución en contextos reales. Responde en español de manera clara y profesional.")
    return analyze_rfp_gemini(rfp_text, category, prompt)       