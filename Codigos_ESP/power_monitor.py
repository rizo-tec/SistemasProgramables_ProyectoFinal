'''
power_monitor_brazalete
Monitorea el estado de carga y voltaje de la batería de 9V.

Integrantes:
- Ángel Ernesto Rizo López
- Diego Alberto Sánchez Infante

Funcion:
Lee el voltaje analógico mediante un divisor de tensión, aplica factores de calibración para la batería 
de 9V y calcula el porcentaje de carga restante para enviarlo al monitor web.
'''

from machine import ADC, Pin
import config

# Configuración del hardware
# Pin ADC en GPIO 3 del ESP32-S3
_adc_pin = Pin(3)
_adc = ADC(_adc_pin)

# Configuración de lectura: 11dB permite un rango de hasta ~3.1V en el pin
_adc.atten(ADC.ATTN_11DB)
_adc.width(ADC.WIDTH_12BIT)

# --- Constantes de Calibración para Sistema de 9V ---
# Se utilizan los valores calculados previamente para tu divisor de voltaje:
# V_REF: Voltaje de referencia medido en el riel de 3.3V
# FACTOR_DIVISION: (R1 + R2) / R2 ajustado por el error del ADC para 8.9V
V_REF = 3.1              # Ajuste para el S3
ADC_MAX = 4095
FACTOR_DIVISION = 11.65  #Factor calculado
OFFSET_VOLTAJE = 0.98    #Cuando no hay pila


def get_voltage():
    try:
        lectura_cruda = 0
        ciclos = 50 
        for _ in range(ciclos):
            lectura_cruda += _adc.read()
        
        promedio = lectura_cruda / ciclos
        
        # Calculamos el voltaje bruto
        voltaje_real = (promedio / ADC_MAX) * V_REF * FACTOR_DIVISION
        
        # Restamos el offset para que marque 0 si no hay pila
        # Si el resultado es menor a 0.5V, asumimos que es 0 (ruido)
        if voltaje_real < 1.2: 
            return 0.0
        return round(voltaje_real, 2)
        
    except Exception as e:
        print("Power Error:", e)
        return 0.0

def get_percentage(voltage):
    """
    Calcula el porcentaje de carga basado en la curva de una bateria de 9V.
    Rango operativo seguro: 9.0V (100%) a 6.8V (0%).
    """
    v_max = 9.0
    v_min = 6.8
    
    if voltage >= v_max:
        return 100
    if voltage <= v_min:
        return 0
    
    porcentaje = ((voltage - v_min) / (v_max - v_min)) * 100
    return int(porcentaje)

def is_low_battery(voltage):
    """
    Verifica si el voltaje ha caido por debajo del umbral de seguridad (7.2V).
    """
    UMBRAL_CRITICO = 7.2
    return voltage < UMBRAL_CRITICO
