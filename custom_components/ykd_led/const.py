DOMAIN = "ykd_led"
DEFAULT_NAME = "YKD-RF Bluetooth LED"
CHARACTERISTIC_UUID = "0000ffd9-0000-1000-8000-00805f9b34fb"

CMD_ON = "cc2333"
CMD_OFF = "cc2433"
CMD_PREFIX = "56"
CMD_SUFFIX = "00f0aa"

# Додаємо список назв для інтерфейсу
EFFECT_NONE = "None"

EFFECTS_MAP = {
    "Strobe": "bb250544",
    "Fade": "bb260544",
    "Slow Flash": "bb270544",
    "Jump": "bb280544"
}