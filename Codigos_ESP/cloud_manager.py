'''
cloud_manager_brazalete
Gestiona la comunicación bidireccional mediante el protocolo MQTT con la nube.

Integrantes:
- Ángel Ernesto Rizo López
- Diego Alberto Sánchez Infante

Funcion:
Establece la conexión con el broker de HiveMQ Cloud y Firebase, permitiendo enviar coordenadas GPS, 
fotos en base64 y recibir comandos remotos para configurar el perímetro o activar la alarma.
'''

import json
import urequests
import config
import time
import actuators
import ubinascii
import gc
import gps_controller
from umqtt.simple import MQTTClient

# --- Configuracion de Temas (Topics) MQTT ---
TOPIC_CONFIG = "brazalete/config"
TOPIC_DATOS = "brazalete/datos"
TOPIC_GPS = "brazalete/gps"
TOPIC_FOTO = "brazalete/camara"
TOPIC_COMANDOS = "brazalete/comandos"
TOPIC_HELLO = "brazalete/hello"
TOPIC_HERE = "brazalete/here"
TOPIC_ZONA_SEGURA = "brazalete/zona_segura"

_client = None

def _mqtt_callback(topic, msg):
    try:
        tema = topic.decode('utf-8')
        mensaje = msg.decode('utf-8').strip()
        
        #Comprobar conexion
        if tema == TOPIC_HELLO:
            if mensaje == "hello?":
                time.sleep_ms(200)
                _client.publish(TOPIC_HERE, "ESP32_ITL: Estoy aquí y funcionando.")
                print("Cloud: Petición de estado respondida.")
                
        #Lógica de Configuración (Zona Segura)
        elif tema == TOPIC_CONFIG:
            data = json.loads(mensaje)
            n_lat = data.get("lat")
            n_lon = data.get("lon")
            n_rango = data.get("rango")
            
            # Actualizamos en el controlador
            gps_controller.update_safe_zone(n_lat, n_lon, n_rango)
            
            # RETROALIMENTACIÓN: Mandamos los nuevos valores al tópico de zona_segura
            publish_safe_zone()
            print(f"Cloud: Zona segura actualizada y confirmada.")
            
        # Lógica del Buzzer
        elif tema == TOPIC_COMANDOS:
            if mensaje == "buzzer_on":
                actuators.set_buzzer_state(True)
                print("Cloud: Buzzer Encendido")
            elif mensaje == "buzzer_off":
                actuators.set_buzzer_state(False)
                print("Cloud: Buzzer Apagado")

    except Exception as e:
        print("Cloud Error: Fallo en callback:", e)


def connect_mqtt():
    global _client
    try:
        # Usamos el hostname 
        _client = MQTTClient(
            client_id=config.MQTT_CLIENT_ID,
            server=config.MQTT_BROKER,
            port=config.MQTT_PORT,
            user=config.MQTT_USER,
            password=config.MQTT_PASS,
            ssl=True,
            ssl_params={'server_hostname': config.MQTT_BROKER}
        )
        _client.set_callback(_mqtt_callback)
        _client.connect()
        _client.subscribe(TOPIC_COMANDOS)
        _client.subscribe(TOPIC_CONFIG)
        _client.subscribe(TOPIC_HELLO)
        print("Cloud: Conectado a MQTT exitosamente.")
        return True
    except Exception as e:
        # El error 5 se captura aqui si las credenciales fallan
        print("Cloud Error: No se pudo conectar a MQTT:", e)
        return False
    
def check_messages():
    """Revisa si hay comandos pendientes en el broker (No bloqueante)."""
    if _client:
        try:
            _client.check_msg()
        except:
            pass

# --- Funciones de Firebase (Historial) ---

def send_to_firebase_consolidated(timestamp_id, data):
    """
    Usa PUT para guardar los datos usando el timestamp como llave.
    Esto agrupa todo (bateria, lat, lon) bajo una misma fecha.
    """
    # La ruta ahora incluye el ID basado en tiempo
    url = f"{config.FB_URL}historial/{timestamp_id}.json?auth={config.FB_TOKEN}"
    try:
        # Usamos PUT en lugar de POST para definir nosotros la llave
        res = urequests.put(url, data=json.dumps(data))
        res.close()
        return True
    except Exception as e:
        print(f"Cloud Error: Firebase fallo:", e)
        return False

# --- Funciones de Envio de Telemetria ---

def publish_data(lat, lon, bat_pct, panic_state):
    t = time.localtime()
    timestamp_id = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])

    # 1. Enviar siempre la Batería y el Estado de Pánico (Tópico de Batería)
    # Usamos un JSON pequeño para la pila
    payload_bat = {
        "bateria": bat_pct,
        "panico": panic_state
    }
    if _client:
        try:
            _client.publish(TOPIC_DATOS, json.dumps(payload_bat), retain=True)
        except: pass

    # 2. FILTRO DE COORDENADAS: Solo enviar si son válidas
    esta_a_salvo = False
    if lat != 0.0 and lon != 0.0:
        
        fuera, distancia = gps_controller.is_outside_safe_zone(lat, lon)
        
        esta_a_salvo = not fuera
        
        payload_gps = {
            "lat": lat,
            "lon": lon,
            "fecha": timestamp_id,
            "zona": esta_a_salvo  
        }
        if _client:
            try:
                # El mapa solo se moverá cuando lleguen datos aquí
                _client.publish(TOPIC_GPS, json.dumps(payload_gps), retain=True)
                print(f"Cloud: Coordenadas válidas enviadas -> {lat}, {lon}")
            except: pass
    else:
        print("Cloud: GPS sin señal (0,0). No se actualizó el mapa para evitar errores.")

    # 3. Firebase (Mantenemos el consolidado para el historial)
    consolidado = {
        "lat": lat, "lon": lon, "bateria": bat_pct, 
        "panico": panic_state, "fecha": timestamp_id
    }
    send_to_firebase_consolidated(timestamp_id, consolidado)
    
def publish_photo(image_bytes):
    """
    Convierte la imagen a Base64 y la envia como texto por MQTT.
    """
    if _client and image_bytes:
        try:
            # 1. Convertir bytes a Base64 (esto genera un string de texto)
            foto_base64 = ubinascii.b2a_base64(image_bytes).decode('utf-8')
            
            # 2. Publicar como texto plano
            _client.publish(TOPIC_FOTO, foto_base64, retain=True)
            print("Cloud: Foto enviada exitosamente en formato Base64.")
            
        except Exception as e:
            print("Cloud Error: Fallo al codificar o enviar foto:", e)

def publish_safe_zone():
    """Envía la configuración actual de la zona segura al monitor."""
    if _client:
        try:
            payload = {
                "lat": gps_controller.SAFE_LAT,
                "lon": gps_controller.SAFE_LON,
                "rango": gps_controller.SAFE_RANGE
            }
            # Usamos retain=True para que el último valor siempre esté disponible en la web
            _client.publish(TOPIC_ZONA_SEGURA, json.dumps(payload), retain=True)
            print("Cloud: Estatus de zona segura enviado.")
        except:
            pass
        
    
def disconnect():
    """Cierra las conexiones de red de forma limpia."""
    global _client
    if _client:
        try:
            _client.disconnect()
            _client = None
        except:
            pass