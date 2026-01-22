'''
storage_manager_brazalete
Administra el guardado de datos y fotos en la tarjeta MicroSD.

Integrantes:
- Ángel Ernesto Rizo López
- Diego Alberto Sánchez Infante

Funcion:
Funciona como la "caja negra" del brazalete, montando el sistema de archivos de la MicroSD para almacenar 
un registro histórico de ubicaciones y copias de seguridad de las fotos capturadas.
'''

import os
import machine
import gc

# Configuración del punto de montaje
MOUNT_POINT = "/sd"

def mount_sd():
    """
    Intenta montar la tarjeta MicroSD utilizando el bus SDMMC.
    Retorna True si el montaje fue exitoso.
    """
    try:
        # El ESP32-S3 utiliza pines especificos para SDMMC (1-bit o 4-bit)
        # En MicroPython, SDCard() intenta inicializar el hardware correspondiente.
        sd = machine.SDCard(slot=1) 
        os.mount(sd, MOUNT_POINT)
        print("Storage: MicroSD montada exitosamente en " + MOUNT_POINT)
        
        # Verificar o crear estructura de carpetas inicial
        _setup_directories()
        return True
    except Exception as e:
        print("Storage: Error al montar MicroSD:", e)
        return False

def _setup_directories():
    """Crea las carpetas necesarias si no existen."""
    try:
        elementos = os.listdir(MOUNT_POINT)
        if "fotos" not in elementos:
            os.mkdir(MOUNT_POINT + "/fotos")
        if "logs" not in elementos:
            os.mkdir(MOUNT_POINT + "/logs")
    except Exception as e:
        print("Storage: Error al crear directorios:", e)

def save_location_log(timestamp, lat, lon, bat):
    """
    Guarda una linea de texto en el historial de ubicacion.
    Formato: CSV para facil lectura posterior en Excel.
    """
    ruta = MOUNT_POINT + "/logs/ubicacion.csv"
    try:
        # Se abre en modo 'append' (a) para no borrar lo anterior
        with open(ruta, "a") as f:
            log_line = f"{timestamp},{lat},{lon},{bat}\n"
            f.write(log_line)
        return True
    except Exception as e:
        print("Storage: Error al escribir log:", e)
        return False

def save_image(image_data, filename):
    """
    Guarda los bytes de una imagen capturada en la carpeta de fotos.
    """
    ruta = MOUNT_POINT + "/fotos/" + filename
    try:
        with open(ruta, "wb") as f:
            f.write(image_data)
        print("Storage: Imagen guardada como " + filename)
        return True
    except Exception as e:
        print("Storage: Error al guardar imagen:", e)
        return False

def get_free_space():
    """Retorna el espacio libre en el sistema de archivos de la SD en KB."""
    try:
        stats = os.statvfs(MOUNT_POINT)
        # f_bavail: bloques libres * f_frsize: tamaño de bloque / 1024
        free_kb = (stats[4] * stats[0]) / 1024
        return free_kb
    except:
        return 0