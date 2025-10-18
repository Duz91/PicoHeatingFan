import network
import time
from umqtt.simple2 import MQTTClient
import secrets

def connect_wifi(timeout_s: int = 30):
    """
    Baut die WLAN-Verbindung auf (STA-Mode) und wartet bis verbunden
    oder bis timeout_s erreicht ist.
    """
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    if not wlan.isconnected():
        print("Verbinde mit WLAN...", end="")
        wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            print(".", end="")
            time.sleep(0.5)
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_s * 1000:
                print()
                raise OSError("WLAN-Verbindung: Timeout")
        print()
    print("WLAN ok. IP:", wlan.ifconfig()[0])

def get_mqtt_client() -> MQTTClient:
    """
    Erstellt einen konfigurierten MQTTClient auf Basis der Angaben in secrets.py
    (ohne Verbindung herzustellen).
    """
    client = MQTTClient(
        client_id=secrets.MQTT_CLIENT_ID,
        server=secrets.MQTT_SERVER,
        port=getattr(secrets, "MQTT_PORT", 1883),
        user=getattr(secrets, "MQTT_USER", None),
        password=getattr(secrets, "MQTT_PASSWORD", None),
        keepalive=getattr(secrets, "MQTT_KEEPALIVE", 60),
        ssl=getattr(secrets, "MQTT_SSL", False),
        ssl_params=getattr(secrets, "MQTT_SSL_PARAMS", {}),
    )
    return client
