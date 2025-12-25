class MainControlUnit:
    def __init__(self, db):
        self.db = db
        self.devices = {}

    def add_device(self, device):
        self.devices[device.thing_id] = device
        self.db.write_log(f"Device added: {device.name}")

    def process_data(self, device_id, value):
        device = self.devices.get(device_id)
        if not device:
            raise ValueError("Device not registered")

        device.set_state(value)
        payload = device.get_data()

        self.db.save_device_state(payload)
        #self.db.write_log(f"Data processed from {device.name}")

        return payload

    def send_alert(self, message: str):
        self.db.write_log(f"ALERT: {message}")
