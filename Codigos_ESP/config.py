'''
config_brazalete
Almacena las credenciales y parámetros estáticos de configuración.

Integrantes:
- Ángel Ernesto Rizo López
- Diego Alberto Sánchez Infante

Funcion:
Centraliza toda la información sensible como nombres de red, contraseñas, URLs de servidores, llaves 
de API y coordenadas iniciales de la casa del paciente.
'''

import json
import os

# Nombre del archivo persistente en la memoria Flash
FILE_NAME = "settings.json"

# --- Valores de Rescate (Fallback) ---
# Estos se usarán solo si el archivo JSON no existe o está corrupto.
_default_settings = {
    "network": {
        "ssid": "Rizo",
        "password": "Rizo1234"
    },
    "mqtt": {
        "broker": "2e0044525b804543a6fe6ab2fcadfa2f.s1.eu.hivemq.cloud",
        "port": 8883,
        "user": "Rizo_",
        "pass": "Rizo1234",
        "client_id": "Brazalete"
    },
    "firebase": {
        "url": "https://brazalete-proyecto-default-rtdb.firebaseio.com/",
        "token": "eOIin9WsCWOt7exlYebCxeDn5ezByWQzQlX7qoXA"
    },
    "safety": {
        "home_lat": 21.119028,
        "home_lon": -101.696426,
        "safe_range_m": 200
    }
}

# --- Variables Globales de Configuración ---
# Se inicializan vacías y se llenan al llamar a load_settings()
WIFI_SSID = ""
WIFI_PASS = ""

MQTT_BROKER = ""
MQTT_PORT = 8883
MQTT_USER = ""
MQTT_PASS = ""
MQTT_CLIENT_ID = ""

FB_URL = ""
FB_TOKEN = ""

HOME_LAT = 0.0
HOME_LON = 0.0
SAFE_RANGE = 0

def load_settings():
    """Carga los datos del JSON a las variables globales de la RAM."""
    global WIFI_SSID, WIFI_PASS, MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASS, MQTT_CLIENT_ID, FB_URL, FB_TOKEN, HOME_LAT, HOME_LON, SAFE_RANGE

    settings = {}
    
    try:
        if FILE_NAME in os.listdir():
            with open(FILE_NAME, "r") as f:
                settings = json.load(f)
            print("Config: Archivo cargado exitosamente.")
        else:
            print("Config: Archivo no encontrado. Usando valores por defecto.")
            settings = _default_settings
            save_settings(settings) # Crea el archivo inicial
            
    except (ValueError, OSError) as e:
        print("Config: Error al leer JSON, restaurando valores por defecto:", e)
        settings = _default_settings

    # Asignación a variables de RAM para acceso rápido
    try:
        WIFI_SSID = settings["network"]["ssid"]
        WIFI_PASS = settings["network"]["password"]
        
        MQTT_BROKER = settings["mqtt"]["broker"]
        MQTT_PORT = settings["mqtt"]["port"]
        MQTT_USER = settings["mqtt"]["user"]
        MQTT_PASS = settings["mqtt"]["pass"]
        MQTT_CLIENT_ID = settings["mqtt"]["client_id"]
        
        FB_URL = settings["firebase"]["url"]
        FB_TOKEN = settings["firebase"]["token"]
        
        HOME_LAT = settings["safety"]["home_lat"]
        HOME_LON = settings["safety"]["home_lon"]
        SAFE_RANGE = settings["safety"]["safe_range_m"]
    except KeyError as e:
        print("Config: Error en la estructura del JSON, falta la llave:", e)

def save_settings(new_settings_dict):
    """Guarda un diccionario de configuracion en el archivo JSON."""
    try:
        with open(FILE_NAME, "w") as f:
            json.dump(new_settings_dict, f)
        print("Config: Cambios persistidos en Flash.")
        # Opcional: Recargar variables en RAM tras guardar
        load_settings()
        return True
    except Exception as e:
        print("Config: Error al guardar en Flash:", e)
        return False

# Carga automatica al importar el modulo
load_settings()