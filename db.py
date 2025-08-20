# --- Control de batches diarios ---
import datetime
import mysql.connector
import os

def get_last_retoma():
    """Obtiene el último offset procesado para el mes actual."""
    conn = get_db_connection2(os.getenv("DB_NAME_PROCESS"))
    cursor = conn.cursor(dictionary=True)
    mes_actual = datetime.date.today().strftime('%Y-%m')
    cursor.execute("SELECT `offset` FROM retoma_log WHERE mes = %s ORDER BY fecha DESC LIMIT 1", (mes_actual,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row['offset'] if row else 0

def update_retoma(offset):
    """Actualiza el offset procesado para el mes actual."""
    conn = get_db_connection2(os.getenv("DB_NAME_PROCESS"))
    cursor = conn.cursor()
    mes_actual = datetime.date.today().strftime('%Y-%m')
    cursor.execute("INSERT INTO retoma_log (mes, `offset`, fecha) VALUES (%s, %s, NOW())", (mes_actual, offset))
    conn.commit()
    cursor.close()
    conn.close()

def cargar_comparendos():
    conn = get_db_connection2(os.getenv("DB_NAME_PROCESS"))
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT codigo, descripcion FROM comparendos")
    lista = cursor.fetchall()
    cursor.close()
    conn.close()
    return {item['codigo']: item['descripcion'] for item in lista}

def crear_comparendo(codigo, descripcion):
    conn = get_db_connection2(os.getenv("DB_NAME_PROCESS"))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comparendos (codigo, descripcion) VALUES (%s, %s)", (codigo, descripcion))
    conn.commit()
    cursor.close()
    conn.close()
def existe_comparendo(documento, numero_comparendo):
    conn = get_db_connection2(os.getenv("DB_NAME_PROCESS"))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM proceso_log WHERE documento = %s AND numero_comparendo = %s LIMIT 1",
        (documento, numero_comparendo)
    )
    existe = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return existe

def insert_proceso(client_id, municipio, placa, documento, celular, numero_comparendo, codigo_comparendo, process_id, estado="pendiente"):
    conn = get_db_connection2(os.getenv("DB_NAME_PROCESS"))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO proceso_log (client_id, municipio, placa, documento, celular, numero_comparendo, codigo_comparendo, process_id, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (client_id, municipio, placa, documento, celular, numero_comparendo, codigo_comparendo, process_id, estado)
    )
    conn.commit()
    cursor.close()
    conn.close()

def update_estado_proceso(process_id, nuevo_estado):
    conn = get_db_connection2(os.getenv("DB_NAME_PROCESS"))
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE proceso_log SET estado = %s WHERE process_id = %s",
        (nuevo_estado, process_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_db_connection(db_name):
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=db_name
    )

def get_db_connection2(db_name):
    return mysql.connector.connect(
        host=os.getenv("DB_HOST2"),
        port=int(os.getenv("DB_PORT2")),
        user=os.getenv("DB_USER2"),
        password=os.getenv("DB_PASSWORD2"),
        database=db_name
    )
