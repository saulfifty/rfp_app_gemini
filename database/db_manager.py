import sqlite3
import hashlib
import re

db_file = 'rfp.db'

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

def guardar_rfp(usuario_id, nombre_archivo, contenido, cliente):
    try:
        from datetime import datetime
        conn = get_connection()
        cursor = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO rfps (usuario_id, cliente, nombre_archivo, contenido, fecha_subida) VALUES (?, ?, ?, ?, ?)",
                    (usuario_id, cliente, nombre_archivo, contenido, fecha))
        conn.commit()
        rfp_id = cursor.lastrowid
        conn.close()
        return rfp_id
    except Exception as e:
        print("Error al guardar RFP:", e)
        return False

def guardar_documento_usuario(rfp_id, titulo, contenido, nombre_categoria, nombre_subcategoria):
    try:
        from datetime import datetime
        conn = get_connection()
        cursor = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("INSERT INTO categorias (rfp_id, nombre) VALUES (?, ?)", (rfp_id, nombre_categoria))
        categoria_id = cursor.lastrowid

        cursor.execute("INSERT INTO subcategorias (nombre, categoria_id) VALUES (?, ?)", (nombre_subcategoria, categoria_id))
        subcategoria_id = cursor.lastrowid

        cursor.execute("INSERT INTO documentos_usuario (rfp_id, titulo, contenido, fecha_creacion, categoria_id, subcategoria_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (rfp_id, titulo, contenido, fecha, categoria_id, subcategoria_id))
        
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
            SELECT 
                documentos_usuario.id,
                documentos_usuario.rfp_id,
                documentos_usuario.titulo,
                documentos_usuario.contenido,
                documentos_usuario.fecha_creacion,
                categorias.nombre AS categoria_nombre,
                subcategorias.nombre AS subcategoria_nombre
            FROM documentos_usuario
            LEFT JOIN categorias ON documentos_usuario.categoria_id = categorias.id
            LEFT JOIN subcategorias ON documentos_usuario.subcategoria_id = subcategorias.id
            WHERE documentos_usuario.rfp_id IN ({})
        '''.format(','.join('?' * len(rfp_ids))), rfp_ids)

        documentos = cursor.fetchall()
        conn.close()
        return documentos
    except Exception as e:
        print("Error al obtener documentos del usuario:", e)
        return []
    
def obtener_todas_rfps_por_usuario(usuario_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id,
                usuario_id,
                cliente,
                nombre_archivo,
                contenido,
                fecha_subida FROM rfps WHERE usuario_id = ?
        ''', (usuario_id,))
        rfps = cursor.fetchall()

        conn.close()
        return rfps
    except Exception as e:
        print("Error al obtener rfps del usuario:", e)
        return []

def obtener_documento_usuario(usuario_id, documento_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                documentos_usuario.id,
                documentos_usuario.rfp_id,
                documentos_usuario.titulo,
                documentos_usuario.contenido,
                documentos_usuario.fecha_creacion,
                categorias.nombre AS categoria_nombre,
                subcategorias.nombre AS subcategoria_nombre
            FROM documentos_usuario
            JOIN rfps ON documentos_usuario.rfp_id = rfps.id
            LEFT JOIN categorias ON documentos_usuario.categoria_id = categorias.id
            LEFT JOIN subcategorias ON documentos_usuario.subcategoria_id = subcategorias.id
            WHERE documentos_usuario.id = ? AND rfps.usuario_id = ?
        ''', (documento_id, usuario_id))
        documento = cursor.fetchone()
        conn.close()
        return documento
    except Exception as e:
        print("Error al obtener documento del usuario:", e)
        return None

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
    
def eliminar_documento_usuario(doc_id, usuario_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT documentos_usuario.categoria_id, documentos_usuario.subcategoria_id
            FROM documentos_usuario
            JOIN rfps ON documentos_usuario.rfp_id = rfps.id
            WHERE documentos_usuario.id = ? AND rfps.usuario_id = ?
        ''', (doc_id, usuario_id))
        resultado = cursor.fetchone()

        if resultado is None:
            print("Documento no pertenece al usuario o no existe.")
            conn.close()
            return False

        categoria_id, subcategoria_id = resultado

        cursor.execute('DELETE FROM documentos_usuario WHERE id = ?', (doc_id,))

        if subcategoria_id:
            cursor.execute('''
                SELECT COUNT(*) FROM documentos_usuario WHERE subcategoria_id = ?
            ''', (subcategoria_id,))
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute('DELETE FROM subcategorias WHERE id = ?', (subcategoria_id,))

        if categoria_id:
            cursor.execute('''
                SELECT COUNT(*) FROM documentos_usuario WHERE categoria_id = ?
            ''', (categoria_id,))
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute('DELETE FROM categorias WHERE id = ?', (categoria_id,))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print("Error al eliminar documento:", e)
        return False
    
def obtener_documentos_por_rfp_y_usuario(rfp_id, usuario_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM rfps
            WHERE id = ? AND usuario_id = ?
        ''', (rfp_id, usuario_id))
        rfp_valida = cursor.fetchone()

        if rfp_valida is None:
            print("La RFP no pertenece al usuario o no existe.")
            conn.close()
            return []

        cursor.execute('''
            SELECT d.id, d.titulo, d.contenido, d.fecha_creacion, c.nombre AS nombre_categoria, s.nombre AS nombre_subcategoria
            FROM documentos_usuario d
            LEFT JOIN categorias c ON d.categoria_id = c.id
            LEFT JOIN subcategorias s ON d.subcategoria_id = s.id
            WHERE d.rfp_id = ?
        ''', (rfp_id,))
        documentos = cursor.fetchall()

        conn.close()
        return documentos

    except Exception as e:
        print("Error al obtener documentos por RFP y usuario:", e)
        return []
    
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

def inicializar_base_de_datos():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        contrasena TEXT NOT NULL
    );''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS rfps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        cliente TEXT,
        nombre_archivo TEXT,
        contenido TEXT,
        fecha_subida TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    );''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        FOREIGN KEY (rfp_id) REFERENCES rfps(id) ON DELETE CASCADE
    );''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS subcategorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria_id INTEGER,
        nombre TEXT NOT NULL,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
    );''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS documentos_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_id INTEGER,
        titulo TEXT,
        contenido TEXT,
        fecha_creacion TEXT,
        categoria_id INTEGER,
        subcategoria_id INTEGER,
        FOREIGN KEY (rfp_id) REFERENCES rfps(id) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
        FOREIGN KEY (subcategoria_id) REFERENCES subcategorias(id) ON DELETE SET NULL
    );''')

    conn.commit()
    conn.close()

    print("DB inicializada")