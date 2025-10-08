import utime
import machine
import dht
from machine import Pin 
from machine import PWM
from time import sleep

pwm = PWM(Pin(15))
pwm.freq(20000)
led = Pin("LED", Pin.OUT)

while True:
    
    led.on()
    d = dht.DHT22(machine.Pin(28))
    d.measure()
    temp = d.temperature()
    hum = d.humidity()
    temp_str = str(temp)
    hum_str = str(hum)
    print(temp_str + ' °C')
    print(hum_str + ' % rel. Luftfeuchte')
    
    
    duty = 4300*temp-87000
    duty_str = str(duty)
    
    print('davor: '+ duty_str)
    
    if duty < 0:
        duty = 0
    elif duty > 65536:
        duty = 65536
        
    percent = 0.00152587890625*duty
    percent = int(percent)
    percent_str = str(percent)
    print('duty: ' + percent_str + '%')
    duty_str = str(duty)
    duty = int(duty)
    print('danach: ' + duty_str)
    pwm.duty_u16(duty)
    led.off()
    sleep(0.5)
    