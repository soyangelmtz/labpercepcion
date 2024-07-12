import machine
import utime
import dht
from math import exp, sqrt

# --- Funciones del Sistema Difuso ---
def normalizar(r, lb, ub):
    return (r - lb) / (ub - lb)

def desnormalizar(n, lb, ub):
    return n * (ub - lb) + lb

def trapezoidmf(x, a, b, c, d):
    return max(min(min((x - a) / (b - a + 0.000001), 1), (d - x) / (d - c + 0.000001)), 0)

def trianglemf(x, a, b, c):
    return max(min((x - a) / (b - a + 0.000001), (c - x) / (c - b + 0.000001)), 0)

def Type1FS(x, n, V):
    a, b, c = V
    if n == 1:
        return trapezoidmf(x, a - 1.0001, a, b, c)
    elif n == 2:
        return trianglemf(x, a, b, c)
    elif n == 3:
        return trianglemf(x, a, b, c)
    elif n == 4:
        return trianglemf(x, a, b, c)
    elif n == 5:
        return trapezoidmf(x, a, b, c, c + 1)
    elif n == 0:
        return 1
    else:
        print("Unknown membership function.")
        return 0

def FuzzySysT1c(X, DB):
    NTRules = len(DB)
    NTI = len(DB[0]) - 1
    PARAM = [
        [0, 0.1666, 0.3333],
        [0.1666, 0.3333, 0.5],
        [0.3333, 0.5, 0.6666],
        [0.5, 0.6666, 0.8333],
        [0.6666, 0.8333, 1]
    ]
    FO = [0 for _ in range(NTRules)]
    for r in range(NTRules):
        sumin = 1
        for i in range(NTI):
            n = DB[r][i]
            if n > 0:
                V = PARAM[DB[r][i] - 1]
            mf = Type1FS(X[i], n, V)
            sumin = min(sumin, mf)
        FO[r] = sumin

    sum1 = 0
    sum2 = 0.00000001
    for dy in range(0, 100, 1):
        ddy = dy / 100
        ss = 0
        for r in range(NTRules):
            n = DB[r][NTI]
            if n > 0:
                V = PARAM[DB[r][NTI] - 1]
            mf = Type1FS(ddy, n, V)
            ss = max(ss, min(mf, FO[r]))
        sum1 += ss * ddy
        sum2 += ss
    return sum1 / sum2

def useFuzzySys(X, DataBase):
    MRange = [
        [0, 50],  # Rango de normalización para la temperatura
        [0, 100],  # Rango de normalización para la humedad
        [0, 100],  # Rango de normalización para la distancia
        [0, 65535],  # Rango de normalización para el LDR
        [0, 65535]  # Rango de normalización para el MQ-135
    ]
    Xn = [normalizar(X[i], MRange[i][0], MRange[i][1]) for i in range(len(X))]
    yn = FuzzySysT1c(Xn, DataBase)
    return desnormalizar(yn, MRange[-1][0], MRange[-1][1])

# --- Configuración de Sensores y Actuadores ---
trig = machine.Pin(14, machine.Pin.OUT)
echo = machine.Pin(15, machine.Pin.IN)
buzzer = machine.Pin(19, machine.Pin.OUT)
pwm = machine.PWM(buzzer)
D4_FREQ = 294

dht_sensor = dht.DHT11(machine.Pin(13))
servo = machine.PWM(machine.Pin(12))
servo.freq(50)

adc_mq135 = machine.ADC(26)
led_verde = machine.Pin(20, machine.Pin.OUT)
led_rojo = machine.Pin(21, machine.Pin.OUT)

adc_ldr = machine.ADC(28)
led_red = machine.Pin(16, machine.Pin.OUT)
led_green = machine.Pin(17, machine.Pin.OUT)
led_blue = machine.Pin(18, machine.Pin.OUT)

THRESHOLD_LOW = 20000
THRESHOLD_MEDIUM = 40000
THRESHOLD_GAS = 10000

def set_servo_angle(angle):
    min_duty = 1000
    max_duty = 9000
    duty = min_duty + (max_duty - min_duty) * angle / 180
    servo.duty_u16(int(duty))

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
    return (duration * 0.0343) / 2

def read_mq135():
    return adc_mq135.read_u16()

def read_ldr():
    return adc_ldr.read_u16()

def set_rgb(red_val, green_val, blue_val):
    led_red.value(red_val)
    led_green.value(green_val)
    led_blue.value(blue_val)

# --- Reglas Difusas ---
DB = [
    [1, 1, 1, 5],
    [5, 0, 0, 1],
    [5, 2, 5, 2],
    [1, 4, 1, 3],
    [2, 3, 2, 4]
]

# --- Función Principal ---
while True:
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidity = dht_sensor.humidity()
    distance = get_distance()
    ldr_value = read_ldr()
    mq135_value = read_mq135()

    inputs = [
        temperature,
        humidity,
        distance,
        ldr_value,
        mq135_value
    ]

    nn_output = useFuzzySys(inputs, DB)
    nn_output = desnormalizar(nn_output, 0, 180)

    print(f"Temp: {temperature}°C, Hum: {humidity}%, Dist: {distance}cm, LDR: {ldr_value}, MQ135: {mq135_value}")
    print(f"NN Output (Servo Angle): {nn_output}")

    if temperature >= 20:
        set_servo_angle(nn_output)

    if distance < 10:
        pwm.freq(D4_FREQ)
        pwm.duty_u16(32768)
    else:
        pwm.duty_u16(0)

    if ldr_value < THRESHOLD_LOW:
        set_rgb(1, 1, 0)
    elif ldr_value < THRESHOLD_MEDIUM:
        set_rgb(1, 0, 1)
    else:
        set_rgb(0, 1, 1)

    if mq135_value > THRESHOLD_GAS:
        led_rojo.value(1)
        led_verde.value(0)
    else:
        led_rojo.value(0)
        led_verde.value(1)

    utime.sleep(1)

