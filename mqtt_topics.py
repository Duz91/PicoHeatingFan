# === MQTT Topics ===


class topics:
    #Eingehende
    TOPIC_STEIGUNG = b"picofan/input/steigung"  # m
    TOPIC_OFFSET   = b"picofan/input/offset"    # b

    #Ausgehende
    MQTT_TOPIC_TEMP = "temperatur"
    MQTT_TOPIC_HUM = "luftfeuchtigkeit"
    MQTT_TOPIC_DUTY = "duty_cycle"
