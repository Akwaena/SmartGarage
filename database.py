import json
from datetime import datetime
from pathlib import Path


class GarageDatabase:
    def __init__(self, filename="garage_db.json"):
        self.file = Path(filename)
        if not self.file.exists():
            self._init_db()

    def _init_db(self):
        data = {
            "devices": {},
            "logs": []
        }
        self._write(data)

    def _read(self):
        return json.loads(self.file.read_text(encoding="utf-8"))

    def _write(self, data):
        self.file.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

    def save_device_state(self, payload: dict):
        data = self._read()
        device_id = str(payload["thing_id"])
        data["devices"][device_id] = payload
        self._write(data)

    def write_log(self, message: str):
        data = self._read()
        data["logs"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message
        })
        self._write(data)

    def get_history(self):
        return self._read()

    def clear(self):
        data = {
            "devices": {},
            "logs": []
        }
        self._write(data)
