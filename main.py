import os
import sys
import random
import string
import requests
import datetime
import json
from dotenv import load_dotenv
from comparendos_api import (login, consultar_info_home_public)
from concurrent.futures import ThreadPoolExecutor
from db import (
    get_db_connection,
    insert_proceso,
    update_retoma,
    update_estado_proceso,
    cargar_comparendos,
    crear_comparendo,
    existe_comparendo,
    get_last_retoma,
    get_registros_pendientes_por_process_template_id
)
from holaamigo import holaamigo_login, holaamigo_template

load_dotenv()
BATCH_SIZE_PROCESS = int(os.getenv("BATCH_SIZE_PROCESS"))
BATCH_SIZE_TEMPLATE = int(os.getenv("BATCH_SIZE_TEMPLATE"))

def get_registros(offset, limit):
    conn = get_db_connection(os.getenv("DB_NAME"))
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, Document, Phone FROM clients WHERE Whatsapp = 2 AND updatedAt >= '2025-11-17' LIMIT %s OFFSET %s", (limit, offset))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_registros_del_dia(fecha):    
    conn = get_db_connection(os.getenv("DB_NAME"))
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, Document, Phone FROM clients WHERE DATE(updatedAt) = %s AND Whatsapp = 2 AND updatedAt >= '2025-11-17'", 
        (fecha,)
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def consultar_municipio(session, municipio, registro, token):
    payload = {
        "criterio": registro.get("Document"),
        "idTipoIdentificacion": "2",
        "response": None,
        "tipoConsulta": "0"
    }
    try:
        response = consultar_info_home_public(municipio, session, token, payload)
        return municipio, response.json(), registro
    except Exception as e:
        print(f"Error en {municipio}: {e}")
        return municipio, None, registro
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

def enviar_templates(usuarios_para_envio, holaamigo_token, process_template_id):
    payload = construir_payload_template(usuarios_para_envio)
    print(f"Payload para el envío {process_template_id}:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    response_envio = holaamigo_template(holaamigo_token, payload)
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Enviando {len(usuarios_para_envio)} templates.")
    if response_envio is None:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error al enviar el template {process_template_id}: la respuesta fue vacía o inválida.")
    else:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Respuesta del envío: {response_envio.get('status')} - {response_envio.get('message')}")
        if response_envio.get("status") == True:
            update_estado_proceso(process_template_id, "completado")

def verificar_comparendos_clientes_nuevos(fecha=None):
    if fecha is None:
        fecha = datetime.datetime.now().strftime('%Y-%m-%d')
    
    print(f"Inicio del proceso diario para fecha {fecha}: [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    
    registros = get_registros_del_dia(fecha)
    
    if not registros:
        print(f"No hay registros nuevos para procesar del día {fecha}.")
        return
    
    print(f"Procesando {len(registros)} registros del día {fecha}")
    
    tokens = {m: login(m) for m in ["BELLO", "ITAGUI", "MEDELLIN", "SABANETA"]}
    process_id = 'D_' + ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    comparendos_dict = cargar_comparendos()

    with requests.Session() as session:
        for j in range(0, len(registros), BATCH_SIZE_TEMPLATE):
            bloque_registros = registros[j:j+BATCH_SIZE_TEMPLATE]
            usuarios_para_envio = []
            process_template_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

            for registro in bloque_registros:
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [
                        executor.submit(consultar_municipio, session, municipio, registro, tokens[municipio])
                        for municipio in tokens
                    ]
                    for future in futures:
                        municipio, data, registro = future.result()

                        if not data:
                            continue

                        consulta = data.get("consultaMultaOComparendoOutDTO", {})
                        comparendos = consulta.get("informacionComparendo", [])
                        for lista, tipo in [(comparendos, "comparendo")]:
                            if lista and isinstance(lista, list) and len(lista) > 0:
                                for item in lista:
                                    numero_comparendo = item.get("numeroComparendo")
                                    fecha_comparendo = item.get("fechaComparendo")
                                    documento = registro.get("Document")
                                    phone = f"+57{registro.get('Phone')}"
                                    placa = item.get("placa")

                                    codigo = None
                                    descripcion = None
                                    estado_cuenta = item.get("estadoCuenta", {})
                                    infracciones = estado_cuenta.get("infraccion", [])
                                    if infracciones and isinstance(infracciones, list) and len(infracciones) > 0:
                                        codigo = infracciones[0].get("codigoInfraccion")
                                        descripcion = infracciones[0].get("descripcion")
                                    if not codigo:
                                        codigo = item.get("codigoInfraccion")
                                    if not descripcion:
                                        descripcion = item.get("descripcionInfraccion")

                                    if not existe_comparendo(documento, numero_comparendo):
                                        if codigo not in comparendos_dict:
                                            crear_comparendo(codigo, descripcion)
                                            comparendos_dict[codigo] = descripcion

                                        usuario_template = {
                                            "phone": phone,
                                            "parameters": [
                                                {"order": 0, "parameter": municipio},
                                                {"order": 1, "parameter": fecha_comparendo},
                                                {"order": 2, "parameter": placa},
                                                {"order": 3, "parameter": codigo},
                                                {"order": 4, "parameter": descripcion}
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
                                            fecha_comparendo,
                                            codigo,
                                            process_id,
                                            process_template_id
                                        )
                                    else:
                                        print(f"El comparendo ya fue notificado previamente Documento: {documento} Comparendo: {numero_comparendo}")
            
            if len(usuarios_para_envio) > 0:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Enviando {len(usuarios_para_envio)} templates para el bloque (process_template_id: {process_template_id})")
                holaamigo_token = holaamigo_login()
                if not holaamigo_token:
                    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No se pudo obtener el token de HolaAmigo. Revisa las credenciales y la conexión.")
                    continue
                enviar_templates(usuarios_para_envio, holaamigo_token, process_template_id)
    
    print(f"Fin del proceso diario: [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

def verificar_comparendos_clientes_antiguos():
    """Verifica comparendos, registra procesos y envía template."""

    offset = get_last_retoma()
    registros = get_registros(offset, BATCH_SIZE_PROCESS)

    if not registros:
        print("No hay más registros para procesar este mes.")
        return
    
    print(f"Inicio del proceso mensual: [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    
    tokens = {m: login(m) for m in ["BELLO", "ITAGUI", "MEDELLIN", "SABANETA"]}
    process_id = 'M_' + ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    comparendos_dict = cargar_comparendos()

    with requests.Session() as session:
        for j in range(0, len(registros), BATCH_SIZE_TEMPLATE):
            bloque_registros = registros[j:j+BATCH_SIZE_TEMPLATE]
            usuarios_para_envio = []
            process_template_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

            for registro in bloque_registros:
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [
                        executor.submit(consultar_municipio, session, municipio, registro, tokens[municipio])
                        for municipio in tokens
                    ]
                    for future in futures:
                        municipio, data, registro = future.result()

                        if not data:
                            continue

                        consulta = data.get("consultaMultaOComparendoOutDTO", {})
                        comparendos = consulta.get("informacionComparendo", [])
                        for lista, tipo in [(comparendos, "comparendo")]:
                            if lista and isinstance(lista, list) and len(lista) > 0:
                                for item in lista:
                                    numero_comparendo = item.get("numeroComparendo")
                                    fecha_comparendo = item.get("fechaComparendo")
                                    documento = registro.get("Document")
                                    phone = f"+57{registro.get('Phone')}"
                                    placa = item.get("placa")

                                    codigo = None
                                    descripcion = None
                                    estado_cuenta = item.get("estadoCuenta", {})
                                    infracciones = estado_cuenta.get("infraccion", [])
                                    if infracciones and isinstance(infracciones, list) and len(infracciones) > 0:
                                        codigo = infracciones[0].get("codigoInfraccion")
                                        descripcion = infracciones[0].get("descripcion")
                                    if not codigo:
                                        codigo = item.get("codigoInfraccion")
                                    if not descripcion:
                                        descripcion = item.get("descripcionInfraccion")

                                    if not existe_comparendo(documento, numero_comparendo):
                                        if codigo not in comparendos_dict:
                                            crear_comparendo(codigo, descripcion)
                                            comparendos_dict[codigo] = descripcion

                                        usuario_template = {
                                            "phone": phone,
                                            "parameters": [
                                                {"order": 0, "parameter": municipio},
                                                {"order": 1, "parameter": fecha_comparendo},
                                                {"order": 2, "parameter": placa},
                                                {"order": 3, "parameter": codigo},
                                                {"order": 4, "parameter": descripcion}
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
                                            fecha_comparendo,
                                            codigo,
                                            process_id,
                                            process_template_id
                                        )
                                    else:
                                        print(f"El comparendo ya fue notificado previamente Documento: {documento} Comparendo: {numero_comparendo}")
            if len(usuarios_para_envio) > 0:
                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Enviando {len(usuarios_para_envio)} templates para el bloque (process_template_id: {process_template_id})")
                holaamigo_token = holaamigo_login()
                if not holaamigo_token:
                    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No se pudo obtener el token de HolaAmigo. Revisa las credenciales y la conexión.")
                    continue
                enviar_templates(usuarios_para_envio, holaamigo_token, process_template_id)

    nuevo_offset = offset + len(registros)
    update_retoma(nuevo_offset)
    print(f"Fin del proceso mensual: [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

def procesar_pendientes_process_template_id(process_template_id):
    registros = get_registros_pendientes_por_process_template_id(process_template_id)
    if not registros:
        print("No hay más registros pendientes para procesar con el process_template_id: ", process_template_id)
        return

    comparendos_dict = cargar_comparendos()
    usuarios_para_envio = []
    for registro in registros:
        phone = registro.get('celular')
        municipio = registro.get('municipio') if 'municipio' in registro else ''
        placa = registro.get('placa') if 'placa' in registro else ''
        codigo = registro.get('codigo_comparendo') if 'codigo_comparendo' in registro else ''
        fecha_comparendo = registro.get('fecha_comparendo') if 'fecha_comparendo' in registro else ''
        descripcion = comparendos_dict.get(codigo, '')

        if codigo:
            usuario_template = {
                "phone": phone,
                "parameters": [
                    {"order": 0, "parameter": municipio},
                    {"order": 1, "parameter": fecha_comparendo},
                    {"order": 2, "parameter": placa},
                    {"order": 3, "parameter": codigo},
                    {"order": 4, "parameter": descripcion}
                ]
            }
            usuarios_para_envio.append(usuario_template)
        

    holaamigo_token = holaamigo_login()
    if not holaamigo_token:
        print("No se pudo obtener el token de HolaAmigo.")
        return

    enviar_templates(usuarios_para_envio, holaamigo_token, process_template_id)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "daily":
            fecha = sys.argv[2] if len(sys.argv) > 2 else None
            verificar_comparendos_clientes_nuevos(fecha)
        elif sys.argv[1] == "monthly":
            verificar_comparendos_clientes_antiguos()
        else:
            # Reprocesar un process_template_id específico
            process_template_id = sys.argv[1]
            procesar_pendientes_process_template_id(process_template_id)
    else:
        print("El parámetro <daily|monthly|process_template_id> es obligatorio.")