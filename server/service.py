# pretvori naprave iz device v model plus definicije operacij

from datetime import datetime, timezone

from spyne import ServiceBase, rpc, Array, Unicode
from spyne.model.fault import Fault

from server.devices import DEVICES, get_device, simulate_reading
from server.models import Device, Sensor, Reading

from server.security import users
from server.security.headers import Security, RegisterUserRequest


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

RANKS = {"reader": 1, "writer": 2}

def _require_role(ctx, required_role):
    header = ctx.in_header
    if header is None or header.UsernameToken is None:
        raise Fault(faultcode="Client", faultstring="Missing security header")

    username = header.UsernameToken.Username
    password = header.UsernameToken.Password.Value
    role = users.verify(username, password)

    if role is None:
        raise Fault(faultcode="Client", faultstring="Invalid username or password")
    if RANKS[role] < RANKS[required_role]:
        raise Fault(faultcode="Client", faultstring="Insufficient rights for this operation")

class ServerRoomService(ServiceBase):
    __namespace__ = "serverroom.soap"
    __in_header__ = Security

    @rpc(_returns=Array(Device))
    def get_device_states(ctx):
        _require_role(ctx, "reader")
        devices = []
        for record in DEVICES.values():
            devices.append(to_device(record))
        return devices

    @rpc(Unicode, Unicode, _returns=None)
    def set_device_state(ctx, serial, state):
        _require_role(ctx, "writer")
        if state not in ("ON", "OFF"):
            raise Fault(faultcode="Client", faultstring="invalid state: " + state)
        try:
            record = get_device(serial)
        except KeyError:
            raise Fault(faultcode="Client", faultstring="unknown device: " + serial)
        record["state"] = state
        return None

    @rpc(Unicode, _returns=Array(Sensor))
    def get_sensors(ctx, serial):
        _require_role(ctx, "reader")
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
        _require_role(ctx, "reader")
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

    @rpc(RegisterUserRequest, _returns=Unicode)
    def register_user(ctx, request):
        try:
            user = users.register(request.username, request.password, request.role)
        except ValueError as error:
            raise Fault(faultcode="Client", faultstring=str(error))
        return user["username"] + " registered as " + user["role"]