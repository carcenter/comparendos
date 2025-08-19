import os
import requests

def holaamigo_login():
    url = os.getenv("HOLA_AMIGO_API_GATEWAY_URL") + "/Auth/Token"
    user = os.getenv("HOLA_AMIGO_API_GATEWAY_USER")
    key = os.getenv("HOLA_AMIGO_API_GATEWAY_KEY")
    payload = {"username": user, "password": key}
    response = requests.post(url, json=payload, verify=False)
    data = response.json()
    token = data.get("token") or data.get("access_token")
    return token

def holaamigo_template(token, plantilla_payload):
    url = os.getenv("HOLA_AMIGO_API_GATEWAY_URL") + "/template"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=plantilla_payload, headers=headers, verify=False)
    return response.json()
