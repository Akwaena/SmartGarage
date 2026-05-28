from flask import Flask, request, jsonify, render_template
import logging

from devices import (
    TemperatureSensor,
    MotionSensor,
    GarageDoor,
    SmartLighting
)
from database import GarageDatabase
from controller import MainControlUnit

import time

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

db = GarageDatabase()
mcu = MainControlUnit(db)
emulator_enabled = False
REPORT_INTERVAL_MINUTES = 5
last_report_ts = time.time()

temperature = TemperatureSensor(1)
motion = MotionSensor(2)
door = GarageDoor(3)
light = SmartLighting(4)

for device in (temperature, motion, door, light):
    mcu.add_device(device)


def make_sensor_report(force=False):
    global last_report_ts

    now = time.time()
    interval = REPORT_INTERVAL_MINUTES * 60

    if not force and now - last_report_ts < interval:
        return False

    temp = None
    motion = None

    for device in mcu.devices.values():
        if device.name == "TemperatureSensor":
            temp = device.value
        elif device.name == "MotionSensor":
            motion = device.value

    if temp is None or motion is None:
        return False

    db.write_log(
        f"Отчёт датчиков:\n"
        f"Температура = {temp} °C,\n"
        f"Движение = {'обнаружено' if motion else 'нет'}"
    )

    last_report_ts = now
    return True


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def api_state():
    make_sensor_report()
    temp_stats = db.get_temperature_stats()
    return jsonify({
        "temperature": temperature.get_data(),
        "motion": motion.get_data(),
        "door": door.get_data(),
        "light": light.get_data(),
        "average_temperature": temp_stats["average"],
        "temperature_count": temp_stats["count"],
        "logs": db.get_history()["logs"][-5:][::-1]
    })


@app.route("/api/device/<int:device_id>", methods=["POST"])
def api_device(device_id):
    make_sensor_report()
    if not emulator_enabled:
        return jsonify({"status": "emulator disabled"}), 403
    data = request.get_json()
    value = data.get("value")

    payload = mcu.process_data(device_id, value)
    logging.info(payload)

    return jsonify(payload), 200


@app.route("/toggle/door", methods=["POST"])
def toggle_door():
    current_state = door.state
    new_state = not current_state

    payload = mcu.process_data(3, new_state)

    db.write_log(
        "Ворота открыты" if new_state else "Ворота закрыты"
    )

    return jsonify(payload), 200


@app.route("/light", methods=["POST"])
def set_light():
    data = request.get_json()
    brightness = int(data.get("brightness", 0))
    state = brightness > 0

    payload = mcu.process_data(
        4,
        {"state": state, "brightness": brightness}
    )

    db.write_log(
        f"Освещение включено ({brightness}%)"
        if state else "Освещение выключено"
    )

    return jsonify(payload), 200

@app.route("/api/log", methods=["POST"])
def api_log():
    make_sensor_report()
    if not emulator_enabled:
        return jsonify({"status": "emulator disabled"}), 403

    data = request.get_json()
    message = data.get("message")

    if message:
        db.write_log(f"[EMULATOR] {message}")

    return jsonify({"status": "ok"})


@app.route("/api/admin/emulator", methods=["POST"])
def toggle_emulator():
    make_sensor_report()
    global emulator_enabled
    emulator_enabled = not emulator_enabled
    db.write_log(f"Эмулятор {'включён' if emulator_enabled else 'выключен'}")
    return jsonify({"enabled": emulator_enabled})

@app.route("/api/admin/clear", methods=["POST"])
def clear_database():
    make_sensor_report()
    db.clear()
    db.write_log("База данных очищена администратором")
    return jsonify({"status": "cleared"})

@app.route("/api/admin/sensor/<int:device_id>", methods=["POST"])
def admin_set_sensor(device_id):
    make_sensor_report()
    data = request.get_json()
    value = data.get("value")

    device = mcu.devices.get(device_id)
    if not device or not hasattr(device, "value"):
        return jsonify({"error": "not a sensor"}), 400

    old = device.value
    device.set_state(value)
    db.save_device_state(device.get_data())
    db.write_log(f"Админ изменил {device.name}: {old} → {value}")

    return jsonify({"status": "ok"})

@app.route("/api/admin/force-report", methods=["POST"])
def force_report():
    ok = make_sensor_report(force=True)

    if ok:
        return jsonify({"status": "report created"})
    return jsonify({"status": "no data"}), 400


if __name__ == "__main__":
    app.run(debug=True)
