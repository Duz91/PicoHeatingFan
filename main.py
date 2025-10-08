import utime
import machine
import dht
from machine import Pin, PWM
import network
import umqtt.simple as mqtt

# WLAN-Konfiguration
WLAN_SSID = "dein_wlan_ssid"
WLAN_PASSWORT = "dein_wlan_passwort"

# MQTT-Konfiguration
MQTT_BROKER = "dein_mqtt_broker"
MQTT_CLIENT_ID = "pico_temp_sensor"
MQTT_TOPIC_TEMP = "temperatur"
MQTT_TOPIC_HUM = "luftfeuchtigkeit"
MQTT_TOPIC_DUTY = "duty_cycle"
MQTT_TOPIC_M = "steigung"
MQTT_TOPIC_B = "achsenabschnitt"

# Standardwerte für m und b
m = 4300
b = -87000

# PWM-Konfiguration
pwm = PWM(Pin(15))
pwm.freq(20000)
led = Pin("LED", Pin.OUT)

# DHT-Konfiguration
d = dht.DHT22(machine.Pin(28))

# WLAN-Verbindung herstellen
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WLAN_SSID, WLAN_PASSWORT)

while not wlan.isconnected():
    print("Verbinde mit WLAN...")
    utime.sleep(1)

print("WLAN verbunden. IP-Adresse:", wlan.ifconfig()[0])

# MQTT-Client erstellen
client = mqtt.MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)

# Callback-Funktion für MQTT-Nachrichten
def sub_cb(topic, msg):
    global m, b
    topic_str = topic.decode('utf-8')
    msg_str = msg.decode('utf-8')
    print((topic_str, msg_str))
    if topic_str == MQTT_TOPIC_M:
        try:
            m = float(msg_str)
            print("Neue Steigung:", m)
        except ValueError:
            print("Ungültige Steigung:", msg_str)
    elif topic_str == MQTT_TOPIC_B:
        try:
            b = float(msg_str)
            print("Neuer Achsenabschnitt:", b)
        except ValueError:
            print("Ungültiger Achsenabschnitt:", msg_str)

client.set_callback(sub_cb)

# Mit MQTT-Broker verbinden
client.connect()
print("Mit MQTT-Broker verbunden")

# Topics abonnieren
client.subscribe(MQTT_TOPIC_M)
client.subscribe(MQTT_TOPIC_B)

# Hauptschleife
while True:
    try:
        led.on()
        d.measure()
        temp = d.temperature()
        hum = d.humidity()

        # Berechnung des Duty Cycle mit den aktuellen Werten für m und b
        duty = int(m * temp + b)

        if duty < 0:
            duty = 0
        elif duty > 65535:
            duty = 65535

        percent = int(0.00152587890625 * duty)

        pwm.duty_u16(duty)

        # Daten an MQTT senden
        client.publish(MQTT_TOPIC_TEMP, str(temp).encode('utf-8'))
        client.publish(MQTT_TOPIC_HUM, str(hum).encode('utf-8'))
        client.publish(MQTT_TOPIC_DUTY, str(percent).encode('utf-8'))

        print("Temperatur:", temp, "°C, Luftfeuchtigkeit:", hum, "%, Duty Cycle:", percent, "%")

        led.off()
        utime.sleep(5) # Sendet alle 5 Sekunden

        # Auf neue MQTT-Nachrichten prüfen
        client.check_msg()

    except Exception as e:
        print("Fehler:", e)
        client.disconnect()
        wlan.disconnect()
        break
