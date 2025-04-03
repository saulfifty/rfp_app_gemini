import sqlite3
import hashlib

def init_db():
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_usuario TEXT UNIQUE,
        contrasena TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS rfps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_archivo TEXT,
        contenido TEXT,
        resumen TEXT,
        pasos_sugeridos TEXT,
        fecha_subida TEXT,
        aprobado BOOLEAN DEFAULT 0
    )''')

    # Verificar si la columna 'resumen' ya existe en la tabla rfps
    cursor.execute("PRAGMA table_info(rfps)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'resumen' not in columns:
        cursor.execute("ALTER TABLE rfps ADD COLUMN resumen TEXT")

    # Verificar columnas y agregar si no existen
    cursor.execute("PRAGMA table_info(rfps)")
    columns = [column[1] for column in cursor.fetchall()]

    if "pasos_sugeridos" not in columns:
        cursor.execute("ALTER TABLE rfps ADD COLUMN pasos_sugeridos TEXT")
        print("Columna 'pasos_sugeridos' añadida.")

    cursor.execute('''CREATE TABLE IF NOT EXISTS respuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_id INTEGER,
        resumen TEXT,
        pasos_sugeridos TEXT,
        fecha_respuesta TEXT,
        FOREIGN KEY (rfp_id) REFERENCES rfps (id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS entrenamiento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_id INTEGER,
        resumen_aprobado TEXT,
        pasos_aprobados TEXT,
        FOREIGN KEY (rfp_id) REFERENCES rfps (id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS evaluacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_id INTEGER,
        analisis_rapido TEXT,
        alineacion_estrategica TEXT,
        ventaja_competitiva TEXT,
        decision_participar TEXT,
        FOREIGN KEY (rfp_id) REFERENCES rfps (id) ON DELETE CASCADE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS propuesta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_id INTEGER,
        estructura_indice TEXT,
        resumen_ejecutivo TEXT,
        solucion_propuesta TEXT,
        beneficios TEXT,
        experiencia TEXT,
        equipo TEXT,
        cronograma TEXT,
        cumplimiento TEXT,
        FOREIGN KEY (rfp_id) REFERENCES rfps (id) ON DELETE CASCADE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS revision (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_id INTEGER,
        revision_interna TEXT,
        aprobacion TEXT,
        FOREIGN KEY (rfp_id) REFERENCES rfps (id) ON DELETE CASCADE
    )''')

    conn.commit()
    conn.close()

def registrar_usuario(nombre_usuario, contrasena):
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(contrasena.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO usuarios (nombre_usuario, contrasena) VALUES (?, ?)", (nombre_usuario, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verificar_credenciales(nombre_usuario, contrasena):
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(contrasena.encode()).hexdigest()
    cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = ? AND contrasena = ?", (nombre_usuario, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def save_rfp_data(nombre_archivo, contenido, resumen, pasos_sugeridos):
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rfps (nombre_archivo, contenido, resumen, pasos_sugeridos, fecha_subida, aprobado) VALUES (?, ?, ?, ?, datetime('now'), 0)", 
                   (nombre_archivo, contenido, resumen, pasos_sugeridos))
    conn.commit()
    rfp_id = cursor.lastrowid
    conn.close()
    return rfp_id

def save_response_data(rfp_id, resumen, pasos_sugeridos):
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO respuestas (rfp_id, resumen, pasos_sugeridos, fecha_respuesta) VALUES (?, ?, ?, datetime('now'))", 
                   (rfp_id, resumen, pasos_sugeridos))
    conn.commit()
    conn.close()

def get_user_rfps(username):
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rfps.nombre_archivo, rfps.contenido, 
               COALESCE(rfps.resumen, 'No hay resumen disponible'),
               COALESCE(rfps.pasos_sugeridos, 'No hay pasos sugeridos'),
               rfps.fecha_subida, rfps.aprobado, 
               COALESCE(respuestas.resumen, 'No hay respuesta disponible'),
               COALESCE(respuestas.pasos_sugeridos, 'No hay pasos en la respuesta')
        FROM rfps
        LEFT JOIN respuestas ON rfps.id = respuestas.rfp_id
    ''')
    
    rows = cursor.fetchall()
    conn.close()

    rfps = [
        {
            "nombre_archivo": row[0],
            "contenido": row[1],
            "resumen": row[2],
            "pasos_sugeridos": row[3],
            "fecha_subida": row[4],
            "aprobado": row[5],
            "resumen_respuesta": row[6],
            "pasos_respuesta": row[7],
        }
        for row in rows
    ]
    return rfps

def save_analysis_data(rfp_id, analisis_rapido, alineacion_estrategica, ventaja_competitiva, decision_participar):
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO evaluacion (rfp_id, analisis_rapido, alineacion_estrategica, ventaja_competitiva, decision_participar)
        VALUES (?, ?, ?, ?, ?)
    """, (rfp_id, analisis_rapido, alineacion_estrategica, ventaja_competitiva, decision_participar))
    conn.commit()
    conn.close()

def save_proposal_data(rfp_id, estructura_indice, resumen_ejecutivo, solucion_propuesta, beneficios, experiencia, equipo, cronograma, cumplimiento):
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO propuesta (rfp_id, estructura_indice, resumen_ejecutivo, solucion_propuesta, beneficios, experiencia, equipo, cronograma, cumplimiento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (rfp_id, estructura_indice, resumen_ejecutivo, solucion_propuesta, beneficios, experiencia, equipo, cronograma, cumplimiento))
    conn.commit()
    conn.close()

def save_review_data(rfp_id, revision_interna, aprobacion):
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO revision (rfp_id, revision_interna, aprobacion)
        VALUES (?, ?, ?)
    """, (rfp_id, revision_interna, aprobacion))
    conn.commit()
    conn.close()