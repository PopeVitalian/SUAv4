import random

DEVICES: dict[str, dict] = {
    "PDU-2026-0001": {
        "serial": "PDU-2026-0001",
        "name": "NetShelter Rack PDU 2026",
        "manufacturer": "APC",
        "state": "ON",
        "sensors": [
            {"serial": "PDU-2026-0001-current", "name": "Total current draw", "unit": "A"},
            {"serial": "PDU-2026-0001-temp", "name": "Rack intake temperature", "unit": "C"},
            {"serial": "PDU-2026-0001-outlet", "name": "Rack plugged outlet", "unit": "1-8", "value": "1"},
        ],
    },
    "ENV-2026-0001": {
        "serial": "ENV-2026-0001",
        "name": "EnvGuard Environmental Sensor SR-100",
        "manufacturer": "Sensirion",
        "state": "ON",
        "sensors": [
            {"serial": "ENV-2026-0001-temperature", "name": "Temperature", "unit": "C"},
            {"serial": "ENV-2026-0001-door", "name": "Door contact", "unit": "enum"},
            {"serial": "ENV-2026-0001-alarm", "name": "Alarm temperature", "unit": "C", "value": "30.0"},
        ],
    },
    "CAM-2026-0001": {
        "serial": "CAM-2026-0001",
        "name": "AxisEye RackCam 4K",
        "manufacturer": "Axis",
        "state": "ON",
        "sensors": [
            {"serial": "CAM-2026-0001-motion", "name": "Motion detected", "unit": "bool"},
            {"serial": "CAM-2026-0001-position", "name": "Camera position", "unit": "door/aisle-a/rack-3", "value": "door"},
        ],
    },
}


# vrne "realno" vrednost za merilni senzor
def simulate_reading(sensor_serial: str) -> str:

    if sensor_serial.endswith("-current"):
        value = random.uniform(2.0, 8.0)
        return str(round(value, 1))

    if sensor_serial.endswith("-temp") or sensor_serial.endswith("-temperature"):
        value = random.uniform(18.0, 28.0)
        return str(round(value, 1))

    if sensor_serial.endswith("-door"):

        roll = random.random()
        if roll < 0.85:
            return "closed"
        elif roll < 0.97:
            return "open"
        else:
            return "fault"

    if sensor_serial.endswith("-motion"):

        roll = random.random()
        if roll < 0.90:
            return "false"
        else:
            return "true"

    raise KeyError("unknown sensor: " + sensor_serial)


def read_sensor_value(sensor: dict) -> str:
    
    if "value" in sensor:
        return sensor["value"]
    return simulate_reading(sensor["serial"])


# vrne serijsko številko naprave
def get_device(serial: str) -> dict:
    return DEVICES[serial]