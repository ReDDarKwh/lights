from gpiozero import DigitalInputDevice
from time import sleep, time
import json
import tinytuya
import itertools

class LightManager:
    
    def __init__(self, config_path='devices.json'):
        with open(config_path, 'r') as f:
            device_configs = json.load(f)
            
        self.first = True

        self.devices = [
            tinytuya.BulbDevice(
                dev_id=cfg['id'],
                address=cfg['ip'],
                local_key=cfg['key'],
                version=3.5
            )
            for cfg in device_configs
        ]

    def turn_on(self, device_id=None):
        """Turn on all devices, or a specific device if device_id is provided."""
        for dev in self.devices:
            if device_id is None or dev.id == device_id:
                dev.turn_on(nowait=True)

    def turn_off(self, device_id=None):
        """Turn off all devices, or a specific device if device_id is provided."""
        for dev in self.devices:
            if device_id is None or dev.id == device_id:
                dev.turn_off(nowait=True)

    def set_color(self, r, g, b, device_id=None):
        """Set RGB color (0-255) for devices."""
        for dev in self.devices:
            if device_id is None or dev.id == device_id:
                dev.set_colour(r, g, b)

    def set_warm_white(self, brightness=100, color_temp=20, device_id=None):
        """Set white mode with custom brightness and warm color temperature (0-100%)."""
        
        for dev in self.devices:
            if device_id is None or dev.id == device_id:
                dev.set_white_percentage(brightness, color_temp, nowait=not self.first)
        self.first = False


if __name__ == '__main__':
    manager = LightManager()

    # GPIO 4 (BCM numbering)
    # pin.is_active == True  -> OFF
    # pin.is_active == False -> ON
    pin = DigitalInputDevice(4, pull_up=False)

    # State variables
    current_state = None  # True for ON, False for OFF
    party_mode = False
    
    # Sequence tracking: stores (state_str, timestamp)
    toggle_history = []

    # Party mode RGB palette
    colors = [
        (255, 0, 0),     # Red
        (0, 255, 0),     # Green
        (0, 0, 255),     # Blue
        (255, 255, 0),   # Yellow
        (255, 0, 255),   # Magenta
        (0, 255, 255),   # Cyan
    ]
    color_cycle = itertools.cycle(colors)

    try:
        while True:
            # Map pin logic: pin.is_active is True -> OFF (False), pin.is_active is False -> ON (True)
            desired_state = not pin.is_active

            # Only execute network commands when state changes
            if desired_state != current_state:
                current_state = desired_state
                now = time()

                state_str = "ON" if current_state else "OFF"
                toggle_history.append((state_str, now))

                # Retain toggles made within the last 5 seconds
                toggle_history = [t for t in toggle_history if now - t[1] <= 5.0]
                recent_sequence = [t[0] for t in toggle_history]

                # Check secret sequence: OFF -> ON -> OFF -> ON
                if len(recent_sequence) >= 4 and recent_sequence[-4:] == ['OFF', 'ON', 'OFF', 'ON']:
                    print("Party mode activated!")
                    party_mode = True
                    toggle_history.clear()

                # Execute state actions
                if not current_state:
                    # Turning OFF stops party mode
                    party_mode = False
                    print("Turning OFF")
                    manager.turn_off()
                elif not party_mode:
                    # Standard ON (Initial startup, post-party mode, or normal toggle)
                    print("Turning ON (Warm White)")
                    manager.turn_on()
                    manager.set_warm_white()

            # Party mode loop while remaining ON
            if party_mode and current_state:
                r, g, b = next(color_cycle)
                manager.set_color(r, g, b)
                sleep(0.3)  # Delay between color swaps
            else:
                sleep(0.1)

    except KeyboardInterrupt:
        pass