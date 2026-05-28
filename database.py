import os
from datetime import datetime, timezone

from pymongo import MongoClient, ASCENDING


DEFAULT_MONGO_URI = "mongodb://localhost:27017/"
DEFAULT_DB_NAME = "smartgarage"

TEMPERATURE_SENSOR_NAME = "TemperatureSensor"


class GarageDatabase:

    def __init__(self, uri=None, db_name=None, client=None):
        if client is not None:
            # Allows injecting a client (e.g. mongomock) in tests.
            self._client = client
        else:
            uri = uri or os.environ.get("MONGO_URI", DEFAULT_MONGO_URI)
            self._client = MongoClient(uri)

        db_name = db_name or os.environ.get("MONGO_DB", DEFAULT_DB_NAME)
        self.db = self._client[db_name]

        self.devices = self.db["devices"]
        self.logs = self.db["logs"]
        self.temperature_readings = self.db["temperature_readings"]

        self._ensure_indexes()

    def _ensure_indexes(self):
        self.devices.create_index("thing_id", unique=True)
        self.logs.create_index([("timestamp", ASCENDING)])
        self.temperature_readings.create_index([("timestamp", ASCENDING)])

    # ----- writes -------------------------------------------------------

    def save_device_state(self, payload: dict):
        thing_id = payload["thing_id"]
        self.devices.update_one(
            {"thing_id": thing_id},
            {"$set": payload},
            upsert=True,
        )

        if (
            payload.get("name") == TEMPERATURE_SENSOR_NAME
            and isinstance(payload.get("value"), (int, float))
            and not isinstance(payload.get("value"), bool)
        ):
            self.temperature_readings.insert_one({
                "value": float(payload["value"]),
                "timestamp": payload.get("timestamp")
                or datetime.now(timezone.utc).isoformat(),
            })

    def write_log(self, message: str):
        self.logs.insert_one({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
        })

    # ----- reads --------------------------------------------------------

    def get_history(self):
        devices = {}
        for doc in self.devices.find({}, {"_id": 0}):
            devices[str(doc["thing_id"])] = doc

        logs = list(
            self.logs.find({}, {"_id": 0}).sort("timestamp", ASCENDING)
        )

        return {"devices": devices, "logs": logs}

    def get_temperature_stats(self):
        count = self.temperature_readings.count_documents({})
        if count == 0:
            return {"average": None, "count": 0}

        result = list(self.temperature_readings.aggregate([
            {"$group": {"_id": None, "average": {"$avg": "$value"}}}
        ]))
        average = round(result[0]["average"], 2) if result else None
        return {"average": average, "count": count}

    # ----- maintenance --------------------------------------------------

    def clear(self):
        self.devices.delete_many({})
        self.logs.delete_many({})
        self.temperature_readings.delete_many({})
