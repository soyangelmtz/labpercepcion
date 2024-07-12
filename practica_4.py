import machine
import utime
import dht
from math import exp, sqrt

# --- Pesos entrenados (copia los valores entrenados de newtest.py) ---
m = [
    [-1.8814794118372211, 1.967958927145107, 0.06481503369783435],
    [0.767825387908019, -0.7912857186975136, -0.10703284669038024],
    [2.5529723919583898, -2.1902218377724076, -0.60794493415699],
    [-0.06582398575160765, 0.4371130930763608, -0.01412587114272335],
    [-0.5912259427369785, 0.35743614574483773, 0.0526456934548353]
]

o = [
    [-2.8526946354561105, 1.1945517101908638, 3.73585365559234, -0.21515574426805137, -0.5707743102775725]
]

MRange = [
    [0, 50],      # Rango de normalización para la temperatura
    [0, 100],     # Rango de normalización para la humedad
    [0, 100],     # Rango de normalización para la distancia
    [0, 65535],   # Rango de normalización para el LDR
    [0, 65535]    # Rango de normalización para el MQ-135
]

# --- Funciones de la Red Neuronal ---
def normalizar(r, lb, ub):
    return (r - lb) / (ub - lb)

def desnormalizar(n, lb, ub):
    return n * (ub - lb) + lb

def fa(x):
    x = min(20, max(-20, x))
    return 1 / (1 + exp(-x))

def ForwardBKG(VI, m, o):
    TMID, TINP, TOUT = len(m), len(m[0]), len(o)
    netm = [sum(m[y][x] * VI[x] for x in range(TINP)) for y in range(TMID)]
    sm = [fa(netm[y]) for y in range(TMID)]
    neto = [sum(o[z][y] * sm[y] for y in range(TMID)) for z in range(TOUT)]
    so = [fa(neto[z]) for z in range(TOUT)]
    return sm, so, neto, netm

def usennbk(X, MRange, m, o):
    TINP = len(X)
    Xn = [normalizar(X[i], MRange[i][0], MRange[i][1]) for i in range(TINP)] + [1]
    sm, so, neto, netm = ForwardBKG(Xn, m, o)
    R = desnormalizar(so[0], MRange[2][0], MRange[2][1])
    return R

# --- Configuración de Sensores y Actuadores ---

# Configuración del sensor HC-SR04
trig = machine.Pin(14, machine.Pin.OUT)
echo = machine.Pin(15, machine.Pin.IN)

# Configuración del buzzer en GP19
buzzer = machine.Pin(19, machine.Pin.OUT)
pwm = machine.PWM(buzzer)

# Frecuencia de la nota RE (D4)
D4_FREQ = 294

def get_distance():
    trig.value(0)
    utime.sleep_us(2)
    trig.value(1)
    utime.sleep_us(10)
    trig.value(0)
    
    while echo.value() == 0:
        pass
    start = utime.ticks_us()
    
    while echo.value() == 1:
        pass
    end = utime.ticks_us()
    
    duration = utime.ticks_diff(end, start)
    distance = (duration * 0.0343) / 2
    return distance

# Configuración del sensor DHT11 en GP13
dht_sensor = dht.DHT11(machine.Pin(13))

# Configuración del servomotor SG90 en GP16
servo = machine.PWM(machine.Pin(12))
servo.freq(50)

def set_servo_angle(angle):
    min_duty = 1000
    max_duty = 9000
    duty = min_duty + (max_duty - min_duty) * angle / 180
    servo.duty_u16(int(duty))

# Configuración del ADC en GP26 para el MQ-135
adc_mq135 = machine.ADC(26)

# Configuración de los LEDs
led_verde = machine.Pin(20, machine.Pin.OUT)
led_rojo = machine.Pin(21, machine.Pin.OUT)

# Configuración del ADC en GP28 para el LDR
adc_ldr = machine.ADC(28)

# Configuración del LED RGB en GP16 (rojo), GP17 (verde), GP18 (azul)
led_red = machine.Pin(16, machine.Pin.OUT)
led_green = machine.Pin(17, machine.Pin.OUT)
led_blue = machine.Pin(18, machine.Pin.OUT)

# Umbrales para diferentes niveles de luz
THRESHOLD_LOW = 20000
THRESHOLD_MEDIUM = 40000

# Umbral para detectar gas
THRESHOLD_GAS = 10000

def read_mq135():
    return adc_mq135.read_u16()

def read_ldr():
    return adc_ldr.read_u16()

def set_rgb(red_val, green_val, blue_val):
    led_red.value(red_val)
    led_green.value(green_val)
    led_blue.value(blue_val)

# --- Función Principal ---

while True:
    # Leer sensores
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidity = dht_sensor.humidity()
    distance = get_distance()
    ldr_value = read_ldr()
    mq135_value = read_mq135()

    # Normalizar entradas
    inputs = [
        normalizar(temperature, MRange[0][0], MRange[0][1]),
        normalizar(humidity, MRange[1][0], MRange[1][1]),
        normalizar(distance, MRange[2][0], MRange[2][1]),
        normalizar(ldr_value, MRange[3][0], MRange[3][1]),
        normalizar(mq135_value, MRange[4][0], MRange[4][1])
    ]

    # Obtener salida de la red neuronal
    nn_output = usennbk(inputs, MRange, m, o)
    
    # Convertir salida a rango adecuado
    nn_output = desnormalizar(nn_output, 0, 180)

    # Imprimir valores para depuración
    print(f"Temp: {temperature}°C, Hum: {humidity}%, Dist: {distance}cm, LDR: {ldr_value}, MQ135: {mq135_value}")
    print(f"NN Output (Servo Angle): {nn_output}")

    # Activar actuadores según la salida de la red neuronal
    set_servo_angle(nn_output)
    
    # Control de buzzer basado en la distancia
    if distance < 10:
        pwm.freq(D4_FREQ)
        pwm.duty_u16(32768)
    else:
        pwm.duty_u16(0)
        
    # Mover servo si la temperatura es mayor o igual a 20 grados
    if temperature >= 20:
        for angle in range(0, 180, 5):
            set_servo_angle(angle)
            utime.sleep(0.02)
        for angle in range(180, 0, -5):
            set_servo_angle(angle)
            utime.sleep(0.02)
    else:
        set_servo_angle(90)  # Posición neutra del servo si la temperatura es menor a 20 grados
    
    
    # Control de LED RGB basado en el valor del LDR
    if ldr_value < THRESHOLD_LOW:
        set_rgb(1, 1, 0)  # Azul
    elif ldr_value < THRESHOLD_MEDIUM:
        set_rgb(1, 0, 1)  # Verde
    else:
        set_rgb(0, 1, 1)  # Rojo

    # Control de LEDs basado en el valor del MQ-135
    if mq135_value > THRESHOLD_GAS:
        led_rojo.value(1)
        led_verde.value(0)
    else:
        led_rojo.value(0)
        led_verde.value(1)
    
    utime.sleep(1)
