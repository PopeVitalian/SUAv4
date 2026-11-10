# pretvori naprave iz device v model plus definicije operacij

from datetime import datetime, timezone

from spyne import ServiceBase, rpc, Array, Unicode
from spyne.model.fault import Fault

from server.devices import DEVICES, get_device, simulate_reading
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
                    value=simulate_reading(s["serial"]),
                )
            )
        return readings