from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st
import hashlib
import re
from datetime import datetime

load_dotenv()

supabase_url = st.secrets["SUPABASE"]["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE"]["SUPABASE_KEY"]

supabase: Client = create_client(supabase_url, supabase_key)

def registrar_usuario(email, password):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        st.write("📬 Respuesta de Supabase al registrar usuario:", response)

        if hasattr(response, "user") and response.user:
            return True
        else:
            st.error("No se pudo registrar el usuario. Revisa la respuesta.")
            return False

    except Exception as e:
        st.error("⚠️ Error al registrar usuario:")
        st.exception(e)
        return False

def login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.write("🔐 Respuesta login:", response)

        if hasattr(response, "user") and response.user:
            return response.user
        else:
            st.error("No se pudo iniciar sesión. ¿Quizás tu correo no está verificado?")
            return None
    except Exception as e:
        st.error("Excepción durante login:")
        st.exception(e)
        return None

def guardar_rfp(usuario_id, nombre_archivo, contenido, cliente):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.write("Datos a insertar en RFP:", {
        "user_id": usuario_id,
        "cliente": cliente,
        "nombre_archivo": nombre_archivo,
        "contenido": contenido,
        "fecha_subida": fecha
    })
    try:
        response = supabase.table("rfps").insert({
            "user_id": usuario_id,
            "cliente": cliente,
            "nombre_archivo": nombre_archivo,
            "contenido": contenido,
            "fecha_subida": fecha
        }).execute()
        st.write("Respuesta de Supabase al guardar RFP:", response)
        return response.data[0]["id"] if response.data else False
    except Exception as e:
        st.error("Error al guardar RFP: " + str(e))
        print("Error al guardar RFP:", e)
        return False

def guardar_documento_usuario(rfp_id, titulo, contenido, nombre_categoria, nombre_subcategoria):
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        categoria_resp = supabase.table("categorias").insert({
            "rfp_id": rfp_id,
            "nombre": nombre_categoria
        }).execute()
        categoria_id = categoria_resp.data[0]["id"]

        subcategoria_resp = supabase.table("subcategorias").insert({
            "categoria_id": categoria_id,
            "nombre": nombre_subcategoria
        }).execute()
        subcategoria_id = subcategoria_resp.data[0]["id"]

        supabase.table("documentos_usuario").insert({
            "rfp_id": rfp_id,
            "titulo": titulo,
            "contenido": contenido,
            "fecha_creacion": fecha,
            "categoria_id": categoria_id,
            "subcategoria_id": subcategoria_id
        }).execute()

        return True
    except Exception as e:
        print("Error al guardar documento:", e)
        return False
    
def obtener_todos_documentos_por_usuario(usuario_id):
    try:
        rfps = supabase.table("rfps").select("id").eq("user_id", usuario_id).execute().data
        if not rfps:
            return []

        rfp_ids = [rfp["id"] for rfp in rfps]

        documentos = supabase.table("documentos_usuario").select("id, rfp_id, titulo, contenido, fecha_creacion, categoria_id, subcategoria_id, categorias(nombre), subcategorias(nombre)").in_("rfp_id", rfp_ids).execute().data
        return documentos
    except Exception as e:
        print("Error al obtener documentos del usuario:", e)
        return []
    
def obtener_todas_rfps_por_usuario(usuario_id):
    try:
        rfps = supabase.table("rfps").select("*").eq("user_id", usuario_id).execute()
        return rfps.data
    except Exception as e:
        print("Error al obtener rfps del usuario:", e)
        return []

def obtener_documento_usuario(usuario_id, documento_id):
    try:
        rfp_check = supabase.table("rfps").select("id").eq("user_id", usuario_id).execute().data
        rfp_ids = [rfp["id"] for rfp in rfp_check]

        documento = supabase.table("documentos_usuario").select("*, categorias(nombre), subcategorias(nombre)").eq("id", documento_id).in_("rfp_id", rfp_ids).execute().data
        return documento[0] if documento else None
    except Exception as e:
        print("Error al obtener documento del usuario:", e)
        return None

def actualizar_documento_usuario(doc_id, nuevo_titulo, nuevo_contenido, usuario_id):
    try:
        nueva_fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        rfp_check = supabase.table("documentos_usuario").select("rfp_id").eq("id", doc_id).execute().data
        if not rfp_check:
            print("Documento no pertenece al usuario.")
            return False

        rfp_id = rfp_check[0]["rfp_id"]
        rfp_valid = supabase.table("rfps").select("id").eq("id", rfp_id).eq("user_id", usuario_id).execute().data

        if not rfp_valid:
            print("La RFP no pertenece al usuario.")
            return False

        supabase.table("documentos_usuario").update({
            "titulo": nuevo_titulo,
            "contenido": nuevo_contenido,
            "fecha_creacion": nueva_fecha
        }).eq("id", doc_id).execute()

        return True
    except Exception as e:
        print("Error al actualizar documento:", e)
        return False
    
def eliminar_documento_usuario(doc_id, usuario_id):
    try:
        documento_resp = supabase.table("documentos_usuario").select("id, categoria_id, subcategoria_id, rfp_id").eq("id", doc_id).execute()
        documento = documento_resp.data[0] if documento_resp.data else None

        if not documento:
            print("Documento no encontrado.")
            return False

        rfp_resp = supabase.table("rfps").select("id").eq("id", documento["rfp_id"]).eq("user_id", usuario_id).execute()
        if not rfp_resp.data:
            print("La RFP no pertenece al usuario.")
            return False

        categoria_id = documento["categoria_id"]
        subcategoria_id = documento["subcategoria_id"]

        supabase.table("documentos_usuario").delete().eq("id", doc_id).execute()

        if subcategoria_id:
            count_resp = supabase.table("documentos_usuario").select("id").eq("subcategoria_id", subcategoria_id).execute()
            if len(count_resp.data) == 0:
                supabase.table("subcategorias").delete().eq("id", subcategoria_id).execute()

        if categoria_id:
            count_resp = supabase.table("documentos_usuario").select("id").eq("categoria_id", categoria_id).execute()
            if len(count_resp.data) == 0:
                supabase.table("categorias").delete().eq("id", categoria_id).execute()

        return True

    except Exception as e:
        print("Error al eliminar documento:", e)
        return False
    
def obtener_documentos_por_rfp_y_usuario(rfp_id, usuario_id):
    try:
        rfp_resp = supabase.table("rfps").select("id").eq("id", rfp_id).eq("user_id", usuario_id).execute()
        if not rfp_resp.data:
            print("La RFP no pertenece al usuario o no existe.")
            return []

        docs_resp = supabase.table("documentos_usuario").select(
            "id, titulo, contenido, fecha_creacion, categorias(nombre), subcategorias(nombre)"
        ).eq("rfp_id", rfp_id).execute()

        return docs_resp.data if docs_resp.data else []

    except Exception as e:
        print("Error al obtener documentos por RFP y usuario:", e)
        return []

def es_correo_valido(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)