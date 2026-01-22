'''
actuators_brazalete
Controla las alertas sonoras y luminosas gestionando los pines de salida.

Integrantes:
- Ángel Ernesto Rizo López
- Diego Alberto Sánchez Infante

Funcion:
Activa el buzzer para la alarma remota y los LEDs de estado; incluye una función especial para recuperar 
el control del pin 15 tras el uso de la cámara.
'''

from machine import Pin, PWM

# --- Configuracion de Hardware ---
# GPIO 15: Buzzer (PWM para control de tono)
# GPIO 14: LED de Alerta (Salida digital)
PIN_BUZZER = 15
_buzzer = Pin(PIN_BUZZER, Pin.OUT)

PIN_LED_BATTERY = 14

# --- Inicializacion ---
_buzzer_pwm = PWM(Pin(PIN_BUZZER))
_buzzer_pwm.duty(0)  # Asegura que inicie en silencio

_led_battery = Pin(PIN_LED_BATTERY, Pin.OUT)
_led_battery.value(0) # Inicia apagado

def set_buzzer_state(state):
    # ESTA LÍNEA ES EL SECRETO: 
    # Forzamos al procesador a reasignar el pin 15 como salida digital AHORA
    buzzer = Pin(15, Pin.OUT) 
    
    if state:
        buzzer.value(1)
        print("Buzzer físico: ON")
    else:
        buzzer.value(0)
        print("Buzzer físico: OFF")

def set_led_battery(state):
    """
    Controla el estado fisico del LED de advertencia de energia.
    La logica de activacion reside en el modulo de monitoreo de potencia.
    """
    _led_battery.value(1 if state else 0)

def emergency_stop():
    """
    Funcion de seguridad para apagar todos los actuadores de inmediato.
    Util en caso de errores criticos o reinicios.
    """
    _buzzer_pwm.duty(0)
    _led_battery.value(0)
    
def reclaim_buzzer():
    """Esta función fuerza al sistema a recuperar el GPIO 15"""
    global _buzzer
    # Declararlo de nuevo como OUT limpia cualquier conexión con la cámara
    _buzzer = Pin(PIN_BUZZER, Pin.OUT)
    _buzzer.value(0)
    print("Hardware: Pin 15 recuperado del bus de cámara.")
