from gpiozero import LED
from time import sleep
import os

led_red = LED(17)
led_green = LED(23)

while True :
    led_red.off()
    led_green.on()
    sleep(14)
