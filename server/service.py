# pretvori naprave iz device v model plus definicije operacij

from datetime import datetime, timezone

from spyne import ServiceBase, rpc, Array, Unicode, Integer, Double
from spyne.model.fault import Fault

from server.devices import DEVICES, get_device, read_sensor_value
from server.models import Device, Sensor, Reading


def to_device(record: dict, include_sensors: bool = False) -> Device:
    sensors = []
    if include_sensors:
        for s in record["sensors"]:
            sensors.append(
                Sensor(
                    serial=s["serial"],
                    name=s["name"],
                    unit=s["unit"],
                )
            )
    return Device(
        serial=record["serial"],
        name=record["name"],
        manufacturer=record["manufacturer"],
        state=record["state"],
        sensors=sensors,
    )


def find_sensor(record: dict, suffix: str):

    for sensor in record["sensors"]:
        if sensor["serial"].endswith(suffix):
            return sensor
    return None


class ServerRoomService(ServiceBase):

    @rpc(_returns=Array(Device))
    def get_device_states(ctx):
        devices = []
        for record in DEVICES.values():
            devices.append(to_device(record))
        return devices

    @rpc(Unicode, Unicode, _returns=None)
    def set_device_state(ctx, serial, state):
        if state not in ("ON", "OFF"):
            raise Fault(faultcode="Client", faultstring="invalid state: " + state)
        try:
            record = get_device(serial)
        except KeyError:
            raise Fault(faultcode="Client", faultstring="unknown device: " + serial)
        record["state"] = state
        return to_device(record)

    @rpc(Unicode, _returns=Array(Sensor))
    def get_sensors(ctx, serial):
        try:
            record = get_device(serial)
        except KeyError:
            raise Fault(faultcode="Client", faultstring="unknown device: " + serial)
        sensors = []
        for s in record["sensors"]:
            sensors.append(
                Sensor(
                    serial=s["serial"],
                    name=s["name"],
                    unit=s["unit"],
                )
            )
        return sensors

    @rpc(Unicode, _returns=Array(Reading))
    def get_readings(ctx, serial):
        try:
            record = get_device(serial)
        except KeyError:
            raise Fault(faultcode="Client", faultstring="unknown device: " + serial)
        now = datetime.now(timezone.utc)
        readings = []
        for s in record["sensors"]:
            readings.append(
                Reading(
                    sensor_serial=s["serial"],
                    timestamp=now,
                    value=read_sensor_value(s),
                )
            )
        return readings

    @rpc(Unicode, Integer, _returns=Device)
    def toggle_outlet(ctx, serial, outlet_index):
        if not (1 <= outlet_index <= 8):
            raise Fault(faultcode="Client", faultstring="outlet_index must be 1..8")
        try:
            record = get_device(serial)
        except KeyError:
            raise Fault(faultcode="Client", faultstring="unknown device: " + serial)
        if not serial.startswith("PDU-"):
            raise Fault(faultcode="Client", faultstring=serial + " has no outlets")
        sensor = find_sensor(record, "-outlet")
        if sensor is not None:
            sensor["value"] = str(outlet_index)
        return to_device(record)

    @rpc(Unicode, Double, _returns=None)
    def set_alarm_temp(ctx, serial, temp_c):
        if temp_c <= 0 or temp_c > 100:
            raise Fault(faultcode="Client", faultstring="temp_c must be in (0, 100]")
        try:
            record = get_device(serial)
        except KeyError:
            raise Fault(faultcode="Client", faultstring="unknown device: " + serial)
        if not serial.startswith("ENV-"):
            raise Fault(faultcode="Client", faultstring=serial + " has no alarm setpoint")
        sensor = find_sensor(record, "-alarm")
        if sensor is not None:
            sensor["value"] = str(round(temp_c, 1))
        return to_device(record)

    @rpc(Unicode, Unicode, _returns=Device)
    def goto_preset(ctx, serial, preset):
        if preset not in ("door", "aisle-a", "rack-3"):
            raise Fault(faultcode="Client", faultstring="invalid preset: " + preset)
        try:
            record = get_device(serial)
        except KeyError:
            raise Fault(faultcode="Client", faultstring="unknown device: " + serial)
        if not serial.startswith("CAM-"):
            raise Fault(faultcode="Client", faultstring=serial + " has no PTZ presets")
        sensor = find_sensor(record, "-position")
        if sensor is not None:
            sensor["value"] = preset
        return to_device(record)