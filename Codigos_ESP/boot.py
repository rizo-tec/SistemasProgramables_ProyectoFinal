'''
boot_brazalete
Estabiliza el voltaje inicial y lanza el script principal del sistema.

Integrantes:

Ángel Ernesto Rizo López

Diego Alberto Sánchez Infante

Funcion:

Se encarga de la limpieza de memoria RAM, establece una pausa de seguridad para estabilizar la energía del ESP32-S3
y ejecuta automáticamente el archivo main.py al encender la placa.import gc
'''

import machine
import os
from machine import WDT

# 1. Optimización de Memoria
# Forzamos una limpieza de RAM inicial para que la cámara tenga espacio
gc.collect()

# 2. Configuración del Watchdog Timer (WDT)
# Ponemos un tiempo de 60 segundos (60000 ms). 
# Es un tiempo largo para permitir que el WiFi y el NTP conecten en main.py sin prisas.
print("Boot: Activando Watchdog Timer (60s)...")
wdt = WDT(timeout=60000)

# 3. Mensaje de bienvenida en consola
print("Boot: Hardware listo. Iniciando Main...")
