import sqlite3
import hashlib
import re

db_file = 'rfp.db'

# Conectar a la base de datos (se creará si no existe)
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Crear las tablas si no existen
cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    contrasena TEXT NOT NULL
);''')

cursor.execute('''CREATE TABLE IF NOT EXISTS rfps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    nombre_archivo TEXT,
    contenido TEXT,
    fecha_subida TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);''')

cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
);''')

cursor.execute('''CREATE TABLE IF NOT EXISTS subcategorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id INTEGER,
    nombre TEXT NOT NULL,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
);''')

cursor.execute('''CREATE TABLE IF NOT EXISTS respuestas_ia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfp_id INTEGER,
    subcategoria_id INTEGER,
    respuesta TEXT,
    fecha_generacion TEXT,
    FOREIGN KEY (rfp_id) REFERENCES rfps(id) ON DELETE CASCADE,
    FOREIGN KEY (subcategoria_id) REFERENCES subcategorias(id) ON DELETE CASCADE
);''')

cursor.execute('''CREATE TABLE IF NOT EXISTS documentos_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfp_id INTEGER,
    titulo TEXT,
    contenido TEXT,
    fecha_creacion TEXT,
    FOREIGN KEY (rfp_id) REFERENCES rfps(id) ON DELETE CASCADE
);''')

# Guardar los cambios y cerrar la conexión
conn.commit()
conn.close()

print("Base de datos y tablas creadas correctamente.")

def get_connection():
    return sqlite3.connect("rfp.db", check_same_thread=False)

def registrar_usuario(nombre_usuario, email, contrasena):
    conn = get_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(contrasena.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO usuarios (nombre, email, contrasena) VALUES (?, ?, ?)", (nombre_usuario, email, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verificar_credenciales(email, contrasena):
    conn = get_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(contrasena.encode()).hexdigest()
    cursor.execute("SELECT * FROM usuarios WHERE email = ? AND contrasena = ?", (email, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def guardar_rfp(usuario_id, nombre_archivo, contenido):
    try:
        from datetime import datetime
        conn = get_connection()
        cursor = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO rfps (usuario_id, nombre_archivo, contenido, fecha_subida) VALUES (?, ?, ?, ?)",
                    (usuario_id, nombre_archivo, contenido, fecha))
        conn.commit()
        rfp_id = cursor.lastrowid
        conn.close()
        return rfp_id
    except Exception as e:
        print("Error al guardar RFP:", e)
        return False

def guardar_respuesta_ia(rfp_id, subcategoria_id, respuesta):
    try:
        from datetime import datetime
        conn = get_connection()
        cursor = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''INSERT INTO respuestas_ia (rfp_id, subcategoria_id, respuesta, fecha_generacion)
                        VALUES (?, ?, ?, ?)''', (rfp_id, subcategoria_id, respuesta, fecha))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al guardar respuesta IA:", e)
        return False

def guardar_documento_usuario(rfp_id, titulo, contenido):
    try:
        from datetime import datetime
        conn = get_connection()
        cursor = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO documentos_usuario (rfp_id, titulo, contenido, fecha_creacion) VALUES (?, ?, ?, ?)",
                    (rfp_id, titulo, contenido, fecha))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al guardar documento:", e)
        return False
    
def obtener_todos_documentos_por_usuario(usuario_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM rfps WHERE usuario_id = ?
        ''', (usuario_id,))
        rfp_ids = cursor.fetchall()

        if not rfp_ids:
            conn.close()
            return []

        rfp_ids = [rfp[0] for rfp in rfp_ids]

        cursor.execute('''
            SELECT documentos_usuario.id, documentos_usuario.rfp_id, 
                   documentos_usuario.titulo, documentos_usuario.contenido, 
                   documentos_usuario.fecha_creacion
            FROM documentos_usuario
            WHERE documentos_usuario.rfp_id IN ({})
        '''.format(','.join('?' * len(rfp_ids))), rfp_ids)

        documentos = cursor.fetchall()
        conn.close()
        return documentos
    except Exception as e:
        print("Error al obtener documentos del usuario:", e)
        return []

def obtener_documento_usuario(usuario_id, rfp_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT documentos_usuario.rfp_id, documentos_usuario.titulo, 
                   documentos_usuario.contenido, documentos_usuario.fecha_creacion
            FROM documentos_usuario
            JOIN rfps ON documentos_usuario.rfp_id = rfps.id
            WHERE documentos_usuario.rfp_id = ? AND rfps.usuario_id = ?
        ''', (rfp_id, usuario_id))
        documentos = cursor.fetchall()
        conn.close()
        return documentos
    except Exception as e:
        print("Error al obtener documentos del usuario:", e)
        return []

def actualizar_documento_usuario(doc_id, nuevo_titulo, nuevo_contenido, usuario_id):
    try:
        from datetime import datetime
        conn = get_connection()
        cursor = conn.cursor()
        nueva_fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Verificamos que el documento pertenece a una RFP del usuario
        cursor.execute('''
            SELECT documentos_usuario.id
            FROM documentos_usuario
            JOIN rfps ON documentos_usuario.rfp_id = rfps.id
            WHERE documentos_usuario.id = ? AND rfps.usuario_id = ?
        ''', (doc_id, usuario_id))
        resultado = cursor.fetchone()

        if resultado is None:
            print("Documento no pertenece al usuario.")
            conn.close()
            return False

        # Si pertenece, actualizamos
        cursor.execute('''
            UPDATE documentos_usuario
            SET titulo = ?, contenido = ?, fecha_creacion = ?
            WHERE id = ?
        ''', (nuevo_titulo, nuevo_contenido, nueva_fecha, doc_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al actualizar documento:", e)
        return False
    
def obtener_user_id_por_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def es_correo_valido(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)