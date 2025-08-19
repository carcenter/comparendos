from holaamigo import holaamigo_login, holaamigo_template
import os
from dotenv import load_dotenv
from db import get_db_connection
from auth import login
import requests
import sys
from db import insert_proceso, update_retoma

load_dotenv()

BATCH_SIZE = 5000

def consumir_api_template(endpoint_env, apikey_env, user_env, pass_env, payload):
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
    # consultar tabla de log para saber dónde quedó
    # si no hay valor, retorna 0
    return 0

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
        "BELLO": login("BELLO"),
        "ITAGUI": login("ITAGUI"),
        "MEDELLIN": login("MEDELLIN"),
        "SABANETA": login("SABANETA"),
    }

    offset = get_last_processed_id()

    import random, string
    process_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    usuarios_para_envio = []
    while True:
        registros = get_registros(offset, BATCH_SIZE)
        if not registros:
            break

        for registro in registros:
            for municipio in tokens:
                # print(f"token: {municipio} {tokens[municipio]}")
                token_sd = tokens[municipio] if municipio in tokens else None
                cookies = {"token_sd": token_sd} if token_sd else None
                payload = {
                    "criterio": registro.get("Document"),
                    "idTipoIdentificacion": "2",  # Ajusta según tu lógica
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
                print("Respuesta API:", data, token_sd, cookies, payload) #TODO remove
                consulta = data.get("consultaMultaOComparendoOutDTO", {})
                comparendos = consulta.get("informacionComparendo", [])
                if comparendos and isinstance(comparendos, list) and len(comparendos) > 0:
                    print("Tiene comparendos:", comparendos)
                    usuario_info = {
                        "id": registro.get("id"),
                        "documento": registro.get("documento"),
                        "municipio": municipio,
                        "comparendos": []
                    }
                    from db import existe_comparendo
                    for comparendo in comparendos:
                        numero_comparendo = comparendo.get("numeroComparendo")
                        documento = registro.get("documento")
                        if not existe_comparendo(documento, numero_comparendo):
                            usuario_info["comparendos"].append({
                                "numeroComparendo": numero_comparendo,
                                # Agrega aquí los demás datos requeridos por la API de plantilla
                            })
                            insert_proceso(
                                registro.get("id"),
                                municipio,
                                documento,
                                numero_comparendo,
                                process_id,
                                "pendiente",
                                "Consulta realizada"
                            )
                            usuarios_para_envio.append(usuario_info)
    # Al final del proceso, después de enviar el template, actualiza el estado a 'completado'
    # Ejemplo de cómo hacerlo:
    holaamigo_token = holaamigo_login()
    response_envio = holaamigo_template(holaamigo_token, {"usuarios": usuarios_para_envio})
    if response_envio.get("success"):
        # update_estado_proceso(process_id, "completado")        
        # update_retoma(registro.get("id"))

        offset += BATCH_SIZE

if __name__ == "__main__":
    verificar_comparendos()
