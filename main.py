import time
import machine
import dht
from machine import Pin, PWM
from mqtt_client import connect_wifi, get_mqtt_client

# === MQTT Topics ===
# Eingehend (m, b)
TOPIC_STEIGUNG = b"picofan/input/steigung"  # m
TOPIC_OFFSET   = b"picofan/input/offset"    # b
# Ausgehend (Telemetrie)
MQTT_TOPIC_TEMP = b"picofan/output/temperatur"
MQTT_TOPIC_HUM  = b"picofan/output/luftfeuchtigkeit"
MQTT_TOPIC_DUTY = b"picofan/output/duty_cycle"

# === Startwerte / State ===
m = 5500.0
b = -121000.0

# === Hardware ===
LED = Pin("LED", Pin.OUT)

# DHT22 an GPIO28 (Pico W)
dht_sensor = dht.DHT22(Pin(28))

# PWM-Fan an GPIO15, 20 kHz
pwm_fan = PWM(Pin(15))
pwm_fan.freq(20_000)

# === Helpers ===
def _to_float(payload: bytes) -> float:
    s = payload.decode("utf-8").strip()
    # optional: deutsches Komma erlauben
    s = s.replace(",", ".")
    return float(s)

def _clamp(val, lo, hi):
    return lo if val < lo else hi if val > hi else val

def on_msg(topic: bytes, msg: bytes, retained: bool, duplicate: bool):
    """MQTT-Callback: setzt m/b aus eingehenden Topics."""
    global m, b
    try:
        if topic == TOPIC_STEIGUNG:
            m = _to_float(msg)
            print("Neue Steigung m:", m, "(retained:", retained, "duplicate:", duplicate, ")")
        elif topic == TOPIC_OFFSET:
            b = _to_float(msg)
            print("Neuer Offset b:", b, "(retained:", retained, "duplicate:", duplicate, ")")
        else:
            print("Unbekanntes Topic:", topic, "Payload:", msg)
    except Exception as e:
        print("Fehler im Callback:", repr(e), "| Topic:", topic, "| Payload:", msg)

def resubscribe(client):
    client.subscribe(TOPIC_STEIGUNG)
    client.subscribe(TOPIC_OFFSET)
    print("Re-subscribed auf:", TOPIC_STEIGUNG, "und", TOPIC_OFFSET)

def read_dht():
    """Liest DHT22, gibt (temp, hum) als float zurück, wirft bei Fehler."""
    dht_sensor.measure()
    return float(dht_sensor.temperature()), float(dht_sensor.humidity())

def apply_pwm_from_temp(temp_c: float):
    """
    Berechnet duty aus y = m*x + b (x = Temperatur in °C) und setzt PWM.
    duty ∈ [0, 65535], zusätzlich Prozentwert (0..100) zurückgeben.
    """
    duty = int(m * temp_c + b)
    duty = _clamp(duty, 0, 65535)
    pwm_fan.duty_u16(duty)
    percent = int((100.0 * duty) / 65535.0)  # ≈ 0.00152587890625 * duty
    return duty, percent

def publish_metrics(client, temp_c: float, hum_pct: float, duty_percent: int):
    try:
        client.publish(MQTT_TOPIC_TEMP, str(temp_c).encode("utf-8"))
        client.publish(MQTT_TOPIC_HUM,  str(hum_pct).encode("utf-8"))
        client.publish(MQTT_TOPIC_DUTY, str(duty_percent).encode("utf-8"))
    except Exception as e:
        print("Publish-Fehler:", repr(e))

def main():
    # WLAN & MQTT-Client – exakt aus Code 1
    connect_wifi()
    client = get_mqtt_client()
    client.set_callback(on_msg)

    # Erstverbindung
    client.connect()
    print("MQTT verbunden.")
    resubscribe(client)
    print("Warte auf MQTT-Nachrichten ...")

    # Loop-Timing: Telemetrie alle 5s, MQTT check ~10 Hz
    next_telemetry = time.ticks_add(time.ticks_ms(), 5000)

    while True:
        try:
            # eingehende MQTT-Nachrichten (nicht blockierend)
            client.check_msg()

            # Telemetrie-/Regel-Intervall
            if time.ticks_diff(time.ticks_ms(), next_telemetry) >= 0:
                try:
                    LED.on()
                    temp, hum = read_dht()
                    duty_u16, duty_pct = apply_pwm_from_temp(temp)
                    publish_metrics(client, temp, hum, duty_pct)
                    print("T={:.1f}°C  RH={:.1f}%  Duty={} ({}%)".format(temp, hum, duty_u16, duty_pct))
                except Exception as se:
                    # DHT manchmal zickig: Fehler einfach loggen und später neu versuchen
                    print("Sensor-/Regel-Fehler:", repr(se))
                finally:
                    LED.off()
                    next_telemetry = time.ticks_add(time.ticks_ms(), 30000)

            time.sleep(0.1)

        except Exception as e:
            # z. B. OSError/ECONNRESET in check_msg()
            print("MQTT-Fehler:", repr(e), "→ Reconnect ...")
            try:
                try:
                    client.disconnect()
                except:
                    pass
                time.sleep(1)
                client.connect()
                resubscribe(client)
                print("Reconnect OK.")
            except Exception as e2:
                print("Reconnect fehlgeschlagen:", repr(e2))
                time.sleep(2)

# Autostart
main()
