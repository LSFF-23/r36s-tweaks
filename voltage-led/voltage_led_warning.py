#!/usr/bin/env python3

import time
import os

VOLTAGE_PATH = "/sys/class/power_supply/battery/voltage_now"
RED_LED      = "/sys/devices/platform/arkos4clone-leds/leds/led-red/brightness"
BLUE_LED     = "/sys/devices/platform/arkos4clone-leds/leds/led-blue/brightness"
CONF_PATH    = "/usr/local/bin/voltage_led_warning.conf"

# Fallback defaults if config is missing or broken
DEFAULT_CRITICAL = 3200000
DEFAULT_LOW      = 3400000

def load_config():
    critical = DEFAULT_CRITICAL
    low      = DEFAULT_LOW
    try:
        with open(CONF_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if key == "CRITICAL":
                    critical = int(val)
                elif key == "LOW":
                    low = int(val)
    except Exception:
        pass  # use defaults if anything goes wrong
    return critical, low

def set_led(path, value):
    with open(path, "w") as f:
        f.write(str(value))

def read_led(path):
    with open(path) as f:
        return int(f.read().strip())

last_mtime = 0
critical, low = load_config()

while True:
    # Reload config if file changed
    try:
        mtime = os.path.getmtime(CONF_PATH)
        if mtime != last_mtime:
            critical, low = load_config()
            last_mtime = mtime
    except Exception:
        pass

    voltage = int(open(VOLTAGE_PATH).read().strip())

    if voltage <= critical:
        set_led(BLUE_LED, 0)
        set_led(RED_LED, 0 if read_led(RED_LED) else 1)
        time.sleep(1)

    elif voltage <= low:
        set_led(BLUE_LED, 0)
        set_led(RED_LED, 1)
        time.sleep(15)

    else:
        set_led(RED_LED, 0)
        set_led(BLUE_LED, 0)
        time.sleep(30)