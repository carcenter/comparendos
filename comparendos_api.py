import requests
import os
import sys

def login(municipio):
    url = f"{os.getenv(municipio + '_API')}/login"
    user = os.getenv(f"{municipio}_USER")
    password = os.getenv(f"{municipio}_PASSWORD")
    verify = municipio != "BELLO"

    try:
        resp = requests.post(url, json={"consumidor": "web", "usuario": user, "password": password}, verify=verify)
        resp.raise_for_status()
        return resp.json()["token"]
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar o autenticar con {municipio}: {e}")
        return None

def consultar_info_home_public(municipio, session, token, payload):
    """
    Realiza la consulta a /home/findInfoHomePublic para el municipio dado.
    """
    cookies = {"token_sd": token} if token else None
    url = f"{os.getenv(municipio + '_API')}/home/findInfoHomePublic"
    verify = municipio != "BELLO"

    try:
        response = session.post(
            url,
            cookies=cookies,
            json=payload,
            verify=verify,
            timeout=30
        )
        return response
    except Exception as e:
        print(f"Error en consulta_info_home_public para {municipio}: {e}")
        return None
