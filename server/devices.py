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
        ],
    },
    "CAM-2026-0001": {
        "serial": "CAM-2026-0001",
        "name": "AxisEye RackCam 4K",
        "manufacturer": "Axis",
        "state": "ON",
        "sensors": [
            {"serial": "CAM-2026-0001-motion", "name": "Motion detected", "unit": "bool"},
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


# vrne serijsko številko naprave
def get_device(serial: str) -> dict:
    return DEVICES[serial]