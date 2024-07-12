import machine
import utime
import dht

# Configuración del sensor HC-SR04
trig = machine.Pin(14, machine.Pin.OUT)
echo = machine.Pin(15, machine.Pin.IN)

# Configuración del buzzer en GP19
buzzer = machine.Pin(19, machine.Pin.OUT)
pwm = machine.PWM(buzzer)

# Frecuencia de la nota RE (D4)
D4_FREQ = 294

def get_distance():
    # Enviar un pulso de 10us al pin Trig
    trig.value(0)
    utime.sleep_us(2)
    trig.value(1)
    utime.sleep_us(10)
    trig.value(0)
    
    # Esperar hasta que el pin Echo se ponga alto
    while echo.value() == 0:
        pass
    start = utime.ticks_us()
    
    # Esperar hasta que el pin Echo se ponga bajo
    while echo.value() == 1:
        pass
    end = utime.ticks_us()
    
    # Calcular la duración del pulso
    duration = utime.ticks_diff(end, start)
    
    # Calcular la distancia en centímetros
    distance = (duration * 0.0343) / 2
    
    return distance

# Configuración del sensor DHT11 en GP13 (pin físico #17)
dht_sensor = dht.DHT11(machine.Pin(13))

# Configuración del servomotor SG90 en GP16 (pin físico #21)
servo = machine.PWM(machine.Pin(12))
servo.freq(50)  # Frecuencia típica para servos

def set_servo_angle(angle):
    # Convertir el ángulo en un ciclo de trabajo de PWM (duty cycle)
    min_duty = 1000  # 1ms pulse corresponds to 0 degrees
    max_duty = 9000  # 2ms pulse corresponds to 180 degrees
    duty = min_duty + (max_duty - min_duty) * angle / 180
    servo.duty_u16(int(duty))

# Configuración del ADC en GP26 (pin físico #31) para el MQ-135
adc_mq135 = machine.ADC(26)

# Configuración de los LEDs
led_verde = machine.Pin(20, machine.Pin.OUT)
led_rojo = machine.Pin(21, machine.Pin.OUT)

# Umbral para detectar gas (ajusta según sea necesario)
THRESHOLD_GAS = 10000

def read_mq135():
    # Leer el valor del ADC (0-65535)
    adc_value = adc_mq135.read_u16()
    return adc_value

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
    # Lectura del sensor HC-SR04
    dist = get_distance()
    print("Distancia: {:.2f} cm".format(dist))
    
    if dist < 10:
        # Encender el buzzer con la nota RE
        pwm.freq(D4_FREQ)
        pwm.duty_u16(32768)  # 50% duty cycle
    else:
        # Apagar el buzzer
        pwm.duty_u16(0)
    
    # Lectura del sensor DHT11
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        
        print("Temperatura: {}°C  Humedad: {}%".format(temperature, humidity))
        
        if temperature > 20:
            # Mover el servo sin parar
            for angle in range(0, 180, 5):
                set_servo_angle(angle)
                utime.sleep(0.02)
            for angle in range(180, 0, -5):
                set_servo_angle(angle)
                utime.sleep(0.02)
        else:
            # Detener el servo en posición neutra si la temperatura es menor o igual a 20 grados
            set_servo_angle(90)
    
    except OSError as e:
        print("Error al leer el sensor DHT11:", e)
    
    # Lectura del sensor MQ-135
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
    
    # Lectura del LDR y control del LED RGB
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

