'''
camera_manager_brazalete
Controla el encendido, precalentamiento y captura de imágenes del sensor OV2640.

Integrantes:
- Ángel Ernesto Rizo López
- Diego Alberto Sánchez Infante

Funcion:
Inicializa el hardware de la cámara, gestiona el tiempo de precalentamiento necesario para el balance 
de blancos y captura las fotos tanto de emergencia como periódicas.
'''

import camera
import time
import gc

def init():
    """
    Inicializa el sensor de la camara usando la configuracion 
    por defecto del firmware que ya probaste.
    """
    try:
        # Intentamos liberar la camara si quedo encendida de una ejecucion previa
        camera.deinit()
    except:
        pass

    # Usamos la inicializacion simple que funciono en tu practica
    # El firmware ya conoce los pines internamente
    success = camera.init()
    
    if success:
        print("Camera: Sensor inicializado correctamente.")
        # Esperamos a que el sensor ajuste la exposicion y el brillo
        time.sleep(2) 
        return True
    else:
        print("Camera: Error al inicializar el sensor.")
        return False

def take_photo():
    """
    Captura una imagen y retorna los bytes en formato JPEG.
    """
    # Liberamos memoria antes de capturar para evitar errores de RAM
    gc.collect() 
    
    img = camera.capture()
    
    if img:
        print("Camera: Imagen capturada con exito.")
        return img
    else:
        print("Camera: Fallo la captura de imagen.")
        return None

def deinit():
    """Libera los recursos de la camara."""
    try:
        camera.deinit()
    except:
        pass