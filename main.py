import os
from dotenv import load_dotenv
from db import get_db_connection
from auth import login_municipio
import requests

load_dotenv()

BATCH_SIZE = 5000

def get_last_processed_id():
    # consultar tabla de log para saber dónde quedó
    # si no hay valor, retorna 0
    return 0

def save_log_entry(registro_id, municipio, documento, estado, mensaje):
    # guardar info en tabla de log
    ...

def get_registros(offset, limit):
    conn = get_db_connection(os.getenv("DB_NAME"))
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clientes LIMIT %s OFFSET %s", (limit, offset))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def verificar_comparendos():
    tokens = {
        "BELLO": login_municipio("BELLO"),
        "ITAGUI": login_municipio("ITAGUI"),
        # "MEDELLIN": login_municipio("MEDELLIN"),
        "SABANETA": login_municipio("SABANETA"),
    }

    offset = get_last_processed_id()

    while True:
        registros = get_registros(offset, BATCH_SIZE)
        if not registros:
            break

        for registro in registros:
            for municipio in tokens:
                print(f"token: {municipio}")
                response = requests.get(
                    f"{os.getenv(f"{municipio}_API")}/home/findInfoHomePublic",
                    # headers={"Authorization": f"Bearer {token}"},
                    verify=False
                )
                data = response.json()
                # procesar data
                print(registro)  # Ver el contenido de cada registro
                save_log_entry(
                    registro.get("id"),  # Ajusta el nombre de la columna si es diferente
                    municipio,
                    registro.get("documento"),  # Ajusta el nombre de la columna si es diferente
                    "pendiente",  # Estado ejemplo
                    "Consulta realizada"  # Mensaje ejemplo
                    )

        offset += BATCH_SIZE

if __name__ == "__main__":
    verificar_comparendos()
