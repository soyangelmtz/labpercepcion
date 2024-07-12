import machine
import utime

# Configuración del ADC en GP26 (pin físico #31) para el MQ-135
adc = machine.ADC(26)

# Configuración de los LEDs
led_verde = machine.Pin(20, machine.Pin.OUT)
led_rojo = machine.Pin(21, machine.Pin.OUT)

# Umbral para detectar gas (ajusta según sea necesario)
THRESHOLD_GAS = 10000

def read_mq135():
    # Leer el valor del ADC (0-65535)
    adc_value = adc.read_u16()
    return adc_value

while True:
    mq135_value = read_mq135()
    print("Valor del MQ-135:", mq135_value)
    
    if mq135_value > THRESHOLD_GAS:
        # Se detecta gas - Encender LED rojo y apagar LED verde
        led_rojo.value(1)
        led_verde.value(0)
        print("Gas detectado!")
    else:
        # Aire limpio - Encender LED verde y apagar LED rojo
        led_rojo.value(0)
        led_verde.value(1)
        print("Aire limpio")
    
    utime.sleep(1)

