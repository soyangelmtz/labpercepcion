import machine
import utime
import dht

# Configuración del sensor DHT11 en GP13 (pin físico #17)
dht_sensor = dht.DHT11(machine.Pin(13))

# Configuración del servomotor SG90 en GP16 (pin físico #16)
servo = machine.PWM(machine.Pin(12))
servo.freq(50)  # Frecuencia típica para servos

def set_servo_angle(angle):
    # Convertir el ángulo en un ciclo de trabajo de PWM (duty cycle)
    min_duty = 1000  # 1ms pulse corresponds to 0 degrees
    max_duty = 9000  # 2ms pulse corresponds to 180 degrees
    duty = min_duty + (max_duty - min_duty) * angle / 180
    servo.duty_u16(int(duty))

while True:
    try:
        # Lectura del sensor DHT11
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        
        print("Temperatura: {}°C  Humedad: {}%".format(temperature, humidity))
        
        if temperature > 30:
            # Mover el servo sin parar
            for angle in range(0, 180, 5):
                set_servo_angle(angle)
                utime.sleep(0.02)
            for angle in range(180, 0, -5):
                set_servo_angle(angle)
                utime.sleep(0.02)
        else:
            # Detener el servo en posición neutra si la temperatura es menor o igual a 30 grados
            set_servo_angle(90)
    
    except OSError as e:
        print("Error al leer el sensor DHT11:", e)
    
    utime.sleep(1)
