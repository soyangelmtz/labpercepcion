import machine
import utime

# Configuración del ADC en GP28 (pin físico #34) para el LDR
adc_ldr = machine.ADC(28)

# Configuración del LED RGB en GP16 (rojo), GP17 (verde), GP18 (azul)
led_red = machine.Pin(16, machine.Pin.OUT)
led_green = machine.Pin(17, machine.Pin.OUT)
led_blue = machine.Pin(18, machine.Pin.OUT)

# Umbrales para diferentes niveles de luz
THRESHOLD_LOW = 20000
THRESHOLD_MEDIUM = 40000

def read_ldr():
    # Leer el valor del ADC (0-65535)
    adc_value = adc_ldr.read_u16()
    return adc_value

def set_rgb(red_val, green_val, blue_val):
    led_red.value(red_val)
    led_green.value(green_val)
    led_blue.value(blue_val)

while True:
    ldr_value = read_ldr()
    print("Valor del LDR:", ldr_value)
    
    if ldr_value < THRESHOLD_LOW:
        # Ambiente oscuro - LED Azul
        set_rgb(1, 1, 0)  # Encender solo el azul
        print("Color: Azul")
    elif ldr_value < THRESHOLD_MEDIUM:
        # Ambiente con luz media - LED Verde
        set_rgb(1, 0, 1)  # Encender solo el verde
        print("Color: Verde")
    else:
        # Ambiente claro - LED Rojo
        set_rgb(0, 1, 1)  # Encender solo el rojo
        print("Color: Rojo")
    
    utime.sleep(1)

