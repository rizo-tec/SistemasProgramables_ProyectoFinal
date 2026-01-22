'''
main_brazalete
Orquestador central que ejecuta el bucle principal y coordina todas las tareas del dispositivo.

Integrantes:
- Ángel Ernesto Rizo López
- Diego Alberto Sánchez Infante

Funcion:
Gestiona el tiempo de ejecución de las tareas no bloqueantes, como la telemetría, el envío de fotos periódicas 
y la detección inmediata del botón de pánico con su respectivo temporizador de 30 segundos.
'''

import time
import machine
import gc
import config
import wifi_manager
import ntptime
import cloud_manager
import gps_controller
import power_monitor
import camera_manager
import storage_manager
import actuators

# --- Configuracion de Tiempos (ms) ---
INTERVALO_TELEMETRIA = 60000  # 1 minuto
INTERVALO_FOTO = 300000       # 5 minutos
INTERVALO_WIFI_CHECK = 10000  # 10 segundos
TIEMPO_WARMUP_CAM = 10000     # 10 segundos de calentamiento

# --- Variables de Estado ---
last_telemetry = time.ticks_ms()
last_photo = time.ticks_ms()
last_wifi_check = time.ticks_ms()

panic_triggered = False
is_panic_warming = False
pánico_activado = False
panic_warmup_start = 0
pánico_inicio_timer = 0
DURACION_PANICO_MS = 30000 # 30 Segundos

def panic_isr(pin):
    """Manejador de interrupcion para el boton de panico."""
    global panic_triggered
    panic_triggered = True
    
# Estados de la cámara
cam_warmup_start = 0
is_cam_warming = False
    
# --- Configuracion del Boton de Panico (Interrupcion) ---
btn_panic = machine.Pin(41, machine.Pin.IN, machine.Pin.PULL_UP)

btn_panic.irq(trigger=machine.Pin.IRQ_FALLING, handler=panic_isr)

# --- Inicializacion de Hardware y Servicios ---
print("Main: Iniciando componentes...")
storage_manager.mount_sd()


# --- Bloqueo hasta Conexión WiFi ---
print("Main: Esperando conexión a Internet obligatoria...")
while not wifi_manager.connect():
    print("Main: Error de red. Reintentando en 5 segundos...")
    time.sleep(5)
    
# --- Sincronización de Hora (UTC-6 León, Gto) ---
def sincronizar_hora():
    try:
        print("Main: Sincronizando hora NTP...")
        ntptime.settime()
        # Ajuste manual de zona horaria (UTC-6)
        # RTC usa segundos. 6 horas = 21600 segundos
        import machine
        rtc = machine.RTC()
        (y, m, d, dw, h, mn, s, ms) = rtc.datetime()
        # Ajustamos la hora restando 6
        rtc.datetime((y, m, d, dw, h - 6, mn, s, ms))
        print("Main: Hora local sincronizada (UTC-6).")
    except:
        print("Main: Error al obtener hora.")
        
sincronizar_hora()
cloud_manager.connect_mqtt()

print("Main: Sistema en línea. Iniciando bucle principal.")

# Recuperar referencia al WDT definida en boot.py (si se activo)
try:
    from boot import wdt
except:
    wdt = None

while True:
    # 1. Alimentar al Watchdog para evitar reinicio
    if wdt:
        wdt.feed()

    # 2. Procesar tareas de fondo (Actualizar GPS y revisar MQTT)
    gps_controller.update()
    cloud_manager.check_messages()
    current_time = time.ticks_ms()

    # 3. Gestion de Reconexion Automatica
    if time.ticks_diff(current_time, last_wifi_check) > INTERVALO_WIFI_CHECK:
        if not wifi_manager.is_connected():
            if wifi_manager.maintain_connection():
                cloud_manager.connect_mqtt()
        last_wifi_check = current_time

    # 4. Tarea A: Telemetria (GPS y Bateria) cada 1 minuto
    if time.ticks_diff(current_time, last_telemetry) > INTERVALO_TELEMETRIA:
        v_bat = power_monitor.get_voltage()
        pct_bat = power_monitor.get_percentage(v_bat)
        pos = gps_controller.get_position()
        print("voltaje = " + str(v_bat))
        print("porcentaje = " + str(pct_bat))
        # Control local del LED de bateria baja
        actuators.set_led_battery(power_monitor.is_low_battery(v_bat))
        
        if pos:
            lat, lon = pos
            # Verificar Punto Seguro
            fuera, dist = gps_controller.is_outside_safe_zone(lat, lon)
            
            print(fuera, dist)
            
            # Enviar a la nube si hay red
            cloud_manager.publish_data(lat, lon, pct_bat, False)
            
            # Guardar en Caja Negra (SD)
            storage_manager.save_location_log(time.time(), lat, lon, pct_bat)
            
            if fuera:
                print(f"ALERTA: Paciente fuera de rango ({dist:.1f}m)")
        else:
            print("Main: GPS buscando señal...")
            # Enviar solo bateria si no hay GPS
            cloud_manager.publish_data(0, 0, pct_bat, False)
            
        last_telemetry = current_time
        gc.collect()

    # 5. Tarea B: Ciclo de Cámara (Warm-up no bloqueante)
    # PASO 1: Iniciar el calentamiento si ya pasó el intervalo
    if not is_cam_warming and time.ticks_diff(current_time, last_photo) > INTERVALO_FOTO:
        print("Cámara: Iniciando warm-up de 10s...")
        if camera_manager.init():
            is_cam_warming = True
            cam_warmup_start = current_time
        else:
            # Si falla el init, lo intentamos de nuevo en 30 segundos, no en 5 minutos
            last_photo = time.ticks_add(current_time, -INTERVALO_FOTO + 30000) 
            print("Cámara: Error de inicio, reintentando pronto...")

    # PASO 2: Capturar la foto una vez cumplido el tiempo de warm-up
    if is_cam_warming and time.ticks_diff(current_time, cam_warmup_start) > TIEMPO_WARMUP_CAM:
        print("Cámara: Tiempo de espera cumplido. Capturando...")
        
        foto = camera_manager.take_photo()
        if foto:
            cloud_manager.publish_photo(foto)
            storage_manager.save_image(foto, f"img_{time.ticks_ms()}.jpg")
            print("Cámara: Foto enviada y guardada.")
        
        # APAGADO Y REINICIO DE ESTADOS
        camera_manager.deinit() 
        is_cam_warming = False
        
        actuators.reclaim_buzzer()
        
        last_photo = current_time  # <--- AQUÍ ESTABA EL ERROR (ahora actualiza la variable correcta)
        
        print("Cámara: Apagada. Próxima foto en 5 minutos.")
        gc.collect()
        
        
    # 6. Gestion de Emergencia (Boton de Panico)
    # PASO 1: Disparo inicial e inicio de warm-up
    if panic_triggered and not is_panic_warming:
        print("Main: ¡BOTON DE PANICO ACTIVADO! Iniciando secuencia...")
        
        pánico_activado = True
        
        pánico_inicio_timer = current_time
        
        # 1. Obtener datos actuales
        v_bat = power_monitor.get_voltage()
        pct_bat = power_monitor.get_percentage(v_bat)
        pos = gps_controller.get_position()
        lat, lon = pos if pos else (0, 0)
        
        # 2. Enviar alerta inmediata a la nube (Sin esperar a la foto)
        cloud_manager.publish_data(lat, lon, pct_bat, True)
        print("Main: Alerta SOS enviada a la nube.")
        
        # 3. Preparar cámara
        if camera_manager.init():
            is_panic_warming = True
            panic_warmup_start = current_time
        else:
            print("Main: Error al iniciar cámara en emergencia.")
        
        panic_triggered = False # Resetear el disparo inicial

    # PASO 2: Captura de la foto SOS tras 5 segundos (No bloqueante)
    if is_panic_warming and time.ticks_diff(current_time, panic_warmup_start) > 5000:
        print("Main: Capturando foto de emergencia...")
        
        foto_sos = camera_manager.take_photo()
        if foto_sos:
            cloud_manager.publish_photo(foto_sos)
            storage_manager.save_image(foto_sos, "SOS_FOTO.jpg")
            print("Main: Foto SOS enviada y guardada.")
        
        camera_manager.deinit()
        is_panic_warming = False
        
        actuators.reclaim_buzzer()
        
        # Resetear el temporizador de fotos normales para evitar una foto doble
        last_photo = current_time 
        
        print("Main: Emergencia procesada. Cámara apagada.")
        gc.collect()
        
    # PASO 3: Desactivar modo panico        
    if pánico_activado and time.ticks_diff(current_time, pánico_inicio_timer) > DURACION_PANICO_MS:
        pánico_activado = False
        print("Main: Estado de pánico finalizado (cooldown terminado).")
        # Enviamos una actualización a la nube indicando que ya terminó el pánico
        cloud_manager.publish_data(lat, lon, pct_bat, False)