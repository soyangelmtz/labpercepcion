import machine
import utime

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

while True:
    dist = get_distance()
    print("Distancia: {:.2f} cm".format(dist))
    
    if dist < 10:
        # Encender el buzzer con la nota RE
        pwm.freq(D4_FREQ)
        pwm.duty_u16(32768)  # 50% duty cycle
    else:
        # Apagar el buzzer
        pwm.duty_u16(0)
    
    utime.sleep(1)

