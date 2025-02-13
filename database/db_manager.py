import sqlite3

def init_db():
    conn = sqlite3.connect("rfp_data.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS rfps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_archivo TEXT,
        contenido TEXT,
        fecha_subida TEXT,
        aprobado BOOLEAN
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS respuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_id INTEGER,
        resumen TEXT,
        pasos_sugeridos TEXT,
        fecha_respuesta TEXT,
        FOREIGN KEY (rfp_id) REFERENCES rfps (id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS entrenamiento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_id INTEGER,
        resumen_aprobado TEXT,
        pasos_aprobados TEXT,
        FOREIGN KEY (rfp_id) REFERENCES rfps (id)
    )''')

    conn.commit()
    conn.close()