import requests
import os
import sys

def login(municipio):
    url = f"{os.getenv(f"{municipio}_API")}/login"
    user = os.getenv(f"{municipio}_USER")
    password = os.getenv(f"{municipio}_PASSWORD")

    try:
        resp = requests.post(url, json={"consumidor": "web", "usuario": user, "password": password}, verify=False)
        resp.raise_for_status()
        return resp.json()["token"]
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar o autenticar con {municipio}: {e}")
        return None
