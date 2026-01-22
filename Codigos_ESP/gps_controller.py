'''
gps_controller_brazalete
Procesa los datos satelitales y calcula la ubicación y distancias de seguridad.

Integrantes:
- Ángel Ernesto Rizo López
- Diego Alberto Sánchez Infante

Funcion:
Lee las sentencias NMEA del módulo GPS y utiliza la fórmula de Haversine para determinar si la ubicación 
actual del paciente se encuentra dentro o fuera del rango seguro establecido.
'''

from machine import UART, Pin
from micropyGPS import MicropyGPS
import math
import config

# Inicializacion de hardware segun pruebas exitosas del usuario
# UART 1, Tx=GPIO 2, Rx=GPIO 1
_uart = UART(1, baudrate=115200, tx=2, rx=1)
_gps = MicropyGPS()

SAFE_LAT = config.HOME_LAT
SAFE_LON = config.HOME_LON
SAFE_RANGE = config.SAFE_RANGE

def update():
    """
    Lee el buffer del UART y actualiza el objeto GPS.
    Debe ser llamado frecuentemente en el bucle principal.
    """
    if _uart.any():
        linea = _uart.readline()
        for char in linea:
            try:
                _gps.update(chr(char))
            except:
                pass

def get_position():
    """
    Calcula y retorna la posicion actual en formato decimal.
    Retorna None si no hay un fix valido de satelites.
    """
    # Verificamos si la latitud es distinta de cero (indicador de señal valida)
    if _gps.latitude[0] == 0:
        return None
    
    # Conversion de formato grados/minutos a decimal
    lat = _gps.latitude[0] + (_gps.latitude[1] / 60)
    if _gps.latitude[2] == 'S': lat = -lat
    
    lon = _gps.longitude[0] + (_gps.longitude[1] / 60)
    if _gps.longitude[2] == 'W': lon = -lon
    
    return lat, lon

def get_satellites():
    """Retorna la cantidad de satelites en uso."""
    return _gps.satellites_in_use

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Implementacion de la Formula de Haversine para calcular 
    la distancia entre dos puntos en metros.
    """
    # Radio de la Tierra en metros
    R = 6371000 
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def is_outside_safe_zone(current_lat, current_lon):
    """
    IMPORTANTE: Aquí usamos las variables SAFE_X que actualiza la nube,
    NO las de config.py directamente.
    """
    global SAFE_LAT, SAFE_LON, SAFE_RANGE
    
    distancia = calculate_distance(
        current_lat, 
        current_lon, 
        SAFE_LAT, 
        SAFE_LON   
    )
    
    # Retornamos si está fuera (True) y la distancia
    fuera = distancia > SAFE_RANGE
    return fuera, distancia

def update_safe_zone(lat, lon, rango):
    """
    Actualiza las coordenadas y el rango del punto seguro.
    Se llama desde cloud_manager al recibir un comando MQTT.
    """
    global SAFE_LAT, SAFE_LON, SAFE_RANGE
    try:
        # Aseguramos que los datos sean del tipo correcto
        SAFE_LAT = float(lat)
        SAFE_LON = float(lon)
        SAFE_RANGE = int(rango)
        
        print(f"GPS_Controller: Perímetro actualizado -> {SAFE_LAT}, {SAFE_LON} ({SAFE_RANGE}m)")
        return True
    except Exception as e:
        print(f"GPS_Controller Error: No se pudo actualizar la zona: {e}")
        return False