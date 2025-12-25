import time
import random
import requests

from devices import (
    TemperatureSensor,
    MotionSensor,
    GarageDoor,
    SmartLighting
)

BASE_URL = "http://127.0.0.1:5000"
PROXIES = {"http": None, "https": None}
INTERVAL = 5


class Emulator:
    def __init__(self):
        self.devices = [
            TemperatureSensor(1),
            MotionSensor(2),
            GarageDoor(3),
            SmartLighting(4)
        ]

    def log(self, message):
        r = requests.post(
            f"{BASE_URL}/api/log",
            json={"message": message},
            proxies=PROXIES,
            timeout=3
        )

        if r.status_code == 403:
            return

    def send(self, device):
        if hasattr(device, "brightness"):  # SmartLighting
            value = {
                "state": device.state,
                "brightness": device.brightness
            }
        elif hasattr(device, "state"):  # GarageDoor
            value = device.state
        else:  # Sensor
            value = device.value

        r = requests.post(
            f"{BASE_URL}/api/device/{device.thing_id}",
            json={"value": value},
            proxies=PROXIES,
            timeout=3
        )
        if r.status_code == 403:
            return

    def emulate_temperature(self):
        sensor = self.devices[0]
        old = sensor.value
        new = round(random.uniform(15, 30), 2)

        sensor.set_state(new)
        self.log(f"{sensor.name}: {old} → {new}")
        self.send(sensor)

    def emulate_motion(self):
        sensor = self.devices[1]
        old = sensor.value
        new = random.choice([True, False])

        sensor.set_state(new)
        self.log(f"{sensor.name}: {old} → {new}")
        self.send(sensor)

    def emulate_door(self):
        actuator = self.devices[2]
        old = actuator.state
        new = not old

        actuator.set_state(new)
        self.log(f"{actuator.name}: {old} → {new}")
        self.send(actuator)

    def emulate_light(self):
        light = self.devices[3]
        old = f"{light.state}, {light.brightness}%"

        brightness = random.choice([0, 25, 50, 75, 100])
        new = f"{brightness > 0}, {brightness}%"

        light.set_state({
            "state": brightness > 0,
            "brightness": brightness
        })

        self.log(f"{light.name}: {old} → {new}")
        self.send(light)

    def run(self):
        self.log("Эмулятор запущен")
        while True:
            self.emulate_temperature()
            self.emulate_motion()
            #self.emulate_door()
            #self.emulate_light()
            time.sleep(INTERVAL)


if __name__ == "__main__":
    Emulator().run()
