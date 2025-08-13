import requests
import os

def login_municipio(municipio):
    url = f"{os.getenv(f"{municipio}_API")}/login"
    user = os.getenv(f"{municipio}_USER")
    password = os.getenv(f"{municipio}_PASSWORD")

    resp = requests.post(url, json={"consumidor": "web", "usuario": user, "password": password}, verify=False)
    print(f"Logging in to {url} with user {user} with password {password} with json: {resp.json()}")
    resp.raise_for_status()
    return resp.json()["token"]
