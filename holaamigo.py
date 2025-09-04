import os
import requests

def holaamigo_login():
    url = os.getenv("HOLA_AMIGO_API_GATEWAY_URL") + "/Auth/Token"
    user = os.getenv("HOLA_AMIGO_API_GATEWAY_USER")
    password = os.getenv("HOLA_AMIGO_API_GATEWAY_PASSWORD")
    key = os.getenv("HOLA_AMIGO_API_GATEWAY_KEY")
    access = os.getenv("HOLA_AMIGO_API_GATEWAY_ACCESS", "IbangMiddlewareApi")

    payload = {
        "user": user,
        "password": password,
        "key": key,
        "access": access
    }

    try:
        response = requests.post(url, json=payload, verify=True)
        response.raise_for_status()
        
        try:
            data = response.json()
        except Exception as e:
            print("Error decoding JSON in login:", e)
            print("Raw response:", response.text)
            return None
        token = data.get("auth_token")
        return token
    except requests.exceptions.RequestException as e:
        print("Login holaamigo request failed:", e)
        return None

def holaamigo_template(token, plantilla_payload):
    url = os.getenv("HOLA_AMIGO_API_GATEWAY_URL") + "/template"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=plantilla_payload, headers=headers, verify=True)
        response.raise_for_status()

        try:
            return response.json()
        except Exception as e:
            print("Error decoding JSON in template:", e)
            print("Raw response:", response.text)
            return None
    except requests.exceptions.RequestException as e:
        print("Template request failed:", e)
        return None
