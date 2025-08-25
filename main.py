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
    existe_comparendo,
    get_last_retoma,
    update_retoma
)
from holaamigo import holaamigo_login, holaamigo_template

load_dotenv()
BATCH_SIZE = int(os.getenv("BATCH_SIZE"))

# Utilidad para construir el payload del template
def construir_payload_template(usuarios):
    """
    Recibe una lista de usuarios con sus datos y construye el payload para la API de template.
    Cada usuario debe tener: phone, parameters (lista de dicts con order y parameter)
    """
    return {
        "users": usuarios,
        "SaveInfo": False,
        "origin": "API",
        "templateName": os.getenv("TEMPLATE_NAME"),
        "language": "ES",
        "sender": "School Center",
        "ParametersName": []
    }

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

def get_registros(offset, limit):
    """Obtiene registros de la tabla clients con paginación."""
    conn = get_db_connection(os.getenv("DB_NAME"))
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clients WHERE Document=42976435 LIMIT %s OFFSET %s", (limit, offset))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def verificar_comparendos():
    """Verifica comparendos, registra procesos y envía template."""

    offset = get_last_retoma()
    registros = get_registros(offset, BATCH_SIZE)

    if not registros:
        print("No hay más registros para procesar este mes.")
        return
    
    tokens = {
        "BELLO": login("BELLO"),
        "ITAGUI": login("ITAGUI"),
        "MEDELLIN": login("MEDELLIN"),
        "SABANETA": login("SABANETA"),
    }
    
    process_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    comparendos_dict = cargar_comparendos()
    usuarios_para_envio = []
    
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
            try:
                response = requests.post(
                    f"{os.getenv(f'{municipio}_API')}/home/findInfoHomePublic",
                    cookies=cookies,
                    json=payload,
                    verify=False,
                    timeout=30
                )
                data = response.json()
            except requests.exceptions.Timeout:
                print(f"Timeout al consultar API de {municipio}. Se omite este registro.")
                continue
            except Exception as e:
                print(f"Error al decodificar JSON para municipio {municipio}: {e}")
                continue

            consulta = data.get("consultaMultaOComparendoOutDTO", {})
            # Procesar informacionComparendo
            comparendos = consulta.get("informacionComparendo", [])
            # Procesar informacionMulta
            multas = consulta.get("informacionMulta", [])

            for lista, tipo in [(comparendos, "comparendo"), (multas, "multa")]:
                if lista and isinstance(lista, list) and len(lista) > 0:
                    for item in lista:
                        numero_comparendo = item.get("numeroComparendo")
                        documento = registro.get("Document")
                        phone = f"+57{registro.get('Phone')}"
                        placa = item.get("placa")
                        
                        # Extraer código y descripción de la infracción desde estadoCuenta.infraccion[0]
                        codigo = None
                        descripcion = None
                        estado_cuenta = item.get("estadoCuenta", {})
                        infracciones = estado_cuenta.get("infraccion", [])
                        if infracciones and isinstance(infracciones, list) and len(infracciones) > 0:
                            codigo = infracciones[0].get("codigoInfraccion")
                            descripcion = infracciones[0].get("descripcion")
                        # Si no hay infracción, intentar usar los campos directos (por compatibilidad)
                        if not codigo:
                            codigo = item.get("codigoInfraccion")

                        if not descripcion:
                            descripcion = item.get("descripcionInfraccion")

                        if not existe_comparendo(documento, numero_comparendo):
                            if codigo not in comparendos_dict:
                                crear_comparendo(codigo, descripcion)
                                comparendos_dict[codigo] = descripcion
                            # Construir usuario para template
                            usuario_template = {
                                "phone": phone,
                                "parameters": [
                                    {"order": 0, "parameter": municipio},
                                    {"order": 1, "parameter": item.get("fechaComparendo")},
                                    {"order": 2, "parameter": placa},
                                    {"order": 3, "parameter": codigo},
                                    {"order": 5, "parameter": descripcion}
                                ]
                            }
                            usuarios_para_envio.append(usuario_template)
                            insert_proceso(
                                registro.get("id"),
                                municipio,
                                placa,
                                documento,
                                phone,
                                numero_comparendo,
                                codigo,
                                process_id,
                                "pendiente"
                            )
    # Enviar template y actualizar estado
    if usuarios_para_envio:
        holaamigo_token = holaamigo_login()
        if not holaamigo_token:
            print("No se pudo obtener el token de HolaAmigo. Revisa las credenciales y la conexión.")
            return
        payload = construir_payload_template(usuarios_para_envio)
        response_envio = holaamigo_template(holaamigo_token, payload)
        if response_envio is None:
            print("Error al enviar el template: la respuesta fue vacía o inválida.")
        else:
            if response_envio.get("status") == "True":
                update_estado_proceso(process_id, "completado")
    # Actualizar offset para el siguiente batch
    nuevo_offset = offset + len(registros)
    update_retoma(nuevo_offset)

if __name__ == "__main__":
    verificar_comparendos()
