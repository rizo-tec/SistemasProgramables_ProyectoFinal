'''
wifi_manager_brazalete
Establece y mantiene la conexión inalámbrica a Internet.

Integrantes:
- Ángel Ernesto Rizo López
- Diego Alberto Sánchez Infante

Funcion:
Se encarga de buscar y conectar el dispositivo a la red Wi-Fi configurada, además de monitorear la señal 
para reconectar automáticamente en caso de pérdida de conexión.
'''

import network
import time
import config
import gc

# Instancia de la interfaz de red
_wlan = network.WLAN(network.STA_IF)

def is_connected():
    """Retorna el estado actual de la conexion."""
    return _wlan.isconnected()

def get_ip():
    """Retorna la direccion IP asignada o None."""
    if _wlan.isconnected():
        return _wlan.ifconfig()[0]
    return None


def connect():
    """
    Intento de conexión con manejo de excepciones para evitar bloqueos.
    """
    try:
        gc.collect()
        # Asegurar que la interfaz esté activa
        if not _wlan.active():
            _wlan.active(True)
        
        if not _wlan.isconnected():
            print("Network: Intentando conectar a " + config.WIFI_SSID + "...")
            # Algunos firmwares lanzan error aquí si la radio está ocupada
            _wlan.connect(config.WIFI_SSID, config.WIFI_PASS)
            
            # Espera de 10 segundos
            for i in range(10):
                if _wlan.isconnected():
                    break
                print(".", end="")l
                time.sleep(1)
            print("") # Salto de línea después de los puntos
                
        if _wlan.isconnected():
            print("Network: Conexión establecida exitosamente.")
            print("Network: IP -> " + str(_wlan.ifconfig()[0]))
            return True
        else:
            print("Network: Tiempo de espera agotado.")
            return False

    except Exception as e:
        print("Network Error: Fallo crítico en el módulo WiFi:", e)
        # Intentamos desactivar para limpiar el estado interno si hubo error
        try:
            _wlan.active(False)
        except:
            pass
        return False
    
def maintain_connection():
    """
    Metodo para el bucle principal. 
    Asegura que la interfaz este activa antes de reconectar.
    """
    if not _wlan.isconnected():
        _wlan.active(True)
        _wlan.connect(config.WIFI_SSID, config.WIFI_PASS)
        return False
    return True

def disconnect():
    """Apaga la interfaz de radio."""
    _wlan.active(False)
    print("Network: WiFi desactivado.")