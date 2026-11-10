# pretvori naprave iz device v model plus definicije operacij

import logging
from datetime import datetime, timezone

from spyne import ServiceBase, rpc, Array, Unicode
from spyne.model.fault import Fault

from server.devices import DEVICES, get_device, simulate_reading
from server.models import Device, Sensor, Reading

from server.security import users
from server.security.headers import Security, RegisterUserRequest

log = logging.getLogger("serverroom")


# kdo kliče (iz WS-Security glave); če glave ni, vrni "?"
def _caller(ctx):
    header = ctx.in_header
    if header is not None and header.UsernameToken is not None:
        return header.UsernameToken.Username
    return "?"


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
        log.warning(" zavrnjen klic za %s: manjka security header", required_role)
        raise Fault(faultcode="Client", faultstring="Missing security header")

    username = header.UsernameToken.Username
    password = header.UsernameToken.Password.Value
    role = users.verify(username, password)

    if role is None:
        log.warning(" zavrnjen klic za %s: napačno geslo (uporabnik %s)", required_role, username)
        raise Fault(faultcode="Client", faultstring="Invalid username or password")
    if RANKS[role] < RANKS[required_role]:
        log.warning(" zavrnjen klic za %s: uporabnik %s ima vlogo %s", required_role, username, role)
        raise Fault(faultcode="Client", faultstring="Insufficient rights for this operation")

class ServerRoomService(ServiceBase):
    __namespace__ = "serverroom.soap"
    __in_header__ = Security

    @rpc(_returns=Array(Device))
    def get_device_states(ctx):
        _require_role(ctx, "reader")
        log.info("klic get_device_states: klicatelj=%s brez argumentov", _caller(ctx))
        devices = []
        for record in DEVICES.values():
            devices.append(to_device(record))
        return devices

    @rpc(Unicode, Unicode, _returns=None)
    def set_device_state(ctx, serial, state):
        _require_role(ctx, "writer")
        log.info("klic set_device_state: klicatelj=%s serial=%s state=%s", _caller(ctx), serial, state)
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
        log.info("klic get_sensors: klicatelj=%s serial=%s", _caller(ctx), serial)
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
        log.info("klic get_readings: klicatelj=%s serial=%s", _caller(ctx), serial)
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
        # gesla ne beležimo
        log.info("klic register_user: klicatelj=%s username=%s role=%s", _caller(ctx), request.username, request.role)
        try:
            user = users.register(request.username, request.password, request.role)
        except ValueError as error:
            raise Fault(faultcode="Client", faultstring=str(error))
        return user["username"] + " registered as " + user["role"]