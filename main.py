import os
import sys
import random
import string
import requests
from dotenv import load_dotenv
from auth import login
from db import (
    get_db_connection,
    insert_proceso,
    update_retoma,
    update_estado_proceso,
    cargar_comparendos,
    crear_comparendo,
    existe_comparendo
)
from holaamigo import holaamigo_login, holaamigo_template

load_dotenv()
BATCH_SIZE = 5000

def consumir_api_template(endpoint_env, apikey_env, user_env, pass_env, payload):
    """Consume una API template con autenticación y retorna la respuesta JSON."""
    url = os.getenv(endpoint_env)
    apikey = os.getenv(apikey_env)
    usuario = os.getenv(user_env)
    password = os.getenv(pass_env)
    headers = {
        "Authorization": f"Bearer {apikey}",
        "Content-Type": "application/json"
    }
    auth = (usuario, password)
    response = requests.post(url, json=payload, headers=headers, auth=auth, verify=False)
    return response.json()

def get_last_processed_id():
    """Consultar tabla de log para saber dónde quedó el proceso. Si no hay valor, retorna 0."""
    return 0

def get_registros(offset, limit):
    """Obtiene registros de la tabla clientes con paginación."""
    conn = get_db_connection(os.getenv("DB_NAME"))
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clientes LIMIT %s OFFSET %s", (limit, offset))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def verificar_comparendos():
    """Verifica comparendos, registra procesos y envía template."""
    tokens = {
        "BELLO": login("BELLO"),
        "ITAGUI": login("ITAGUI"),
        "MEDELLIN": login("MEDELLIN"),
        "SABANETA": login("SABANETA"),
    }
    offset = get_last_processed_id()
    process_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    comparendos_dict = cargar_comparendos()
    usuarios_para_envio = []
    while True:
        registros = get_registros(offset, BATCH_SIZE)
        if not registros:
            break
        for registro in registros:
            for municipio in tokens:
                token_sd = tokens[municipio]
                cookies = {"token_sd": token_sd} if token_sd else None
                payload = {
                    "criterio": registro.get("Document"),
                    "idTipoIdentificacion": "2",
                    "response": None,
                    "tipoConsulta": "0"
                }
                response = requests.post(
                    f"{os.getenv(f'{municipio}_API')}/home/findInfoHomePublic",
                    cookies=cookies,
                    json=payload,
                    verify=False
                )
                data = response.json()
                consulta = data.get("consultaMultaOComparendoOutDTO", {})
                comparendos = consulta.get("informacionComparendo", [])
                if comparendos and isinstance(comparendos, list) and len(comparendos) > 0:
                    usuario_info = {
                        "id": registro.get("id"),
                        "documento": registro.get("documento"),
                        "municipio": municipio,
                        "comparendos": []
                    }
                    for comparendo in comparendos:
                        numero_comparendo = comparendo.get("numeroComparendo")
                        documento = registro.get("documento")
                        if not existe_comparendo(documento, numero_comparendo):
                            codigo = comparendo.get("codigoInfraccion")
                            descripcion = comparendo.get("descripcionInfraccion")
                            if codigo not in comparendos_dict:
                                crear_comparendo(codigo, descripcion)
                                comparendos_dict[codigo] = descripcion
                            usuario_info["comparendos"].append({
                                "numeroComparendo": numero_comparendo,
                                "codigo": codigo,
                                "descripcion": descripcion
                            })
                            insert_proceso(
                                registro.get("id"),
                                municipio,
                                registro.get("placa"),
                                documento,
                                numero_comparendo,
                                codigo,
                                process_id,
                                "pendiente"
                            )
                    usuarios_para_envio.append(usuario_info)
        # Enviar template y actualizar estado
        if usuarios_para_envio:
            holaamigo_token = holaamigo_login()
            response_envio = holaamigo_template(holaamigo_token, {"usuarios": usuarios_para_envio})
            if response_envio.get("success"):
                update_estado_proceso(process_id, "completado")
        offset += BATCH_SIZE

if __name__ == "__main__":
    verificar_comparendos()
