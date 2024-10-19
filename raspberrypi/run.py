import os
from gpiozero import LED
from time import sleep
import signal
import sys

led_red = LED(17)
led_green = LED(23)

def cleanup(signal_received, frame):
    led_red.off()
    led_green.off()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

try:
    while True:
        led_red.on()
        sleep(20)
        led_red.off()
        led_green.on()
        sleep(10)
        led_green.off()
except Exception as e:
    cleanup(None, None)
