from gpiozero import DigitalInputDevice
from time import sleep

# GPIO 4 (BCM numbering)
pin = DigitalInputDevice(4, pull_up=False)

try:
    while True:
        print("ON" if pin.is_active else "OFF")
        sleep(0.5)
except KeyboardInterrupt:
    pass