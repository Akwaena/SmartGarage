from abc import ABC, abstractmethod
from datetime import datetime

class AbstractThing(ABC):
    def __init__(self, thing_id: int, name: str):
        self.thing_id = thing_id
        self.name = name

    @abstractmethod
    def get_data(self) -> dict:
        pass

    @abstractmethod
    def set_state(self, state):
        pass


class Sensor(AbstractThing):
    def __init__(self, thing_id: int, name: str, unit: str):
        super().__init__(thing_id, name)
        self.unit = unit
        self.value = None
        self.timestamp = None

    def read_value(self, value):
        self.value = value
        self.timestamp = datetime.utcnow()

    def set_state(self, state):
        self.read_value(state)

    def get_data(self) -> dict:
        return {
            "thing_id": self.thing_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class TemperatureSensor(Sensor):
    def __init__(self, thing_id: int):
        super().__init__(thing_id, "TemperatureSensor", "°C")


class MotionSensor(Sensor):
    def __init__(self, thing_id: int):
        super().__init__(thing_id, "MotionSensor", "boolean")


class Actuator(AbstractThing):
    def __init__(self, thing_id: int, name: str):
        super().__init__(thing_id, name)
        self.state = False
        self.last_activation = None

    def activate(self):
        self.state = True
        self.last_activation = datetime.utcnow()

    def deactivate(self):
        self.state = False
        self.last_activation = datetime.utcnow()

    def set_state(self, state: bool):
        if state:
            self.activate()
        else:
            self.deactivate()

    def get_data(self) -> dict:
        return {
            "thing_id": self.thing_id,
            "name": self.name,
            "state": self.state,
            "last_activation": self.last_activation.isoformat()
            if self.last_activation else None
        }


class GarageDoor(Actuator):
    def __init__(self, thing_id: int):
        super().__init__(thing_id, "GarageDoor")


class SmartLighting(Actuator):
    def __init__(self, thing_id: int):
        super().__init__(thing_id, "SmartLighting")
        self.brightness = 0  # 0–100 %

    def set_state(self, state):
        if isinstance(state, dict):
            self.state = state.get("state", self.state)
            self.brightness = max(0, min(100, state.get("brightness", self.brightness)))
        else:
            super().set_state(state)

        self.last_activation = datetime.utcnow()

    def get_data(self) -> dict:
        data = super().get_data()
        data["brightness"] = self.brightness
        return data

