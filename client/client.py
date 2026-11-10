#!/usr/bin/env python3
# console client, prej zaženi run_server.py

from zeep import Client
from zeep.exceptions import Fault, TransportError


WSDL = "http://127.0.0.1:8007/?wsdl"
TNS = "serverroom.soap"  # ciljni imenski prostor storitve (glej server/app.py)


def print_menu(session):
    print()
    print("=== Server Room SOAP Client ===")
    if session["username"]:
        print("  (prijavljen kot: " + session["username"] + ")")
    print("1) Prikaži stanja vseh naprav")
    print("2) Nastavi stanje naprave (ON/OFF)")
    print("3) Prikaži senzorje naprave")
    print("4) Prikaži meritve naprave")
    print("5) Registriraj novega uporabnika")
    print("6) Prijava (nastavi WSSE poverilnice)")
    print("7) Demo klici (vse operacije + 2 namerni napaki)")
    print("0) Izhod")


def make_header(client, username, password):
    security = client.get_element("{%s}Security" % TNS)
    return security(
        UsernameToken={
            "Username": username,
            "Password": {"Value": password},
        }
    )


def require_login(session):
    if session["header"] is None:
        print("  Najprej se prijavi (izbira 6) — operacija zahteva WSSE security header.")
        return False
    return True


def op_states(service, session):
    if not require_login(session):
        return
    devices = service.get_device_states(_soapheaders=[session["header"]])
    print()
    for device in devices:
        print("  " + device["serial"] + "  " + device["name"] + "  stanje=" + str(device["state"]))


def op_set_state(service, session):
    if not require_login(session):
        return
    serial = input("  Serijska številka naprave: ").strip()
    state = input("  Novo stanje (ON/OFF): ").strip().upper()
    service.set_device_state(serial, state, _soapheaders=[session["header"]])
    print("  OK: " + serial + " -> " + state)


def op_sensors(service, session):
    if not require_login(session):
        return
    serial = input("  Serijska številka naprave: ").strip()
    sensors = service.get_sensors(serial, _soapheaders=[session["header"]])
    print()
    for sensor in sensors:
        print("    - " + sensor["serial"] + "  (" + sensor["name"] + ", enota=" + sensor["unit"] + ")")


def op_readings(service, session):
    if not require_login(session):
        return
    serial = input("  Serijska številka naprave: ").strip()
    readings = service.get_readings(serial, _soapheaders=[session["header"]])
    print()
    for reading in readings:
        print("    - " + reading["sensor_serial"] + " @ " + str(reading["timestamp"]) + " -> " + str(reading["value"]))


def op_register(service, session):
    username = input("  Uporabniško ime (min 3 znake): ").strip()
    password = input("  Geslo (min 6 znakov): ").strip()
    role = input("  Vloga (reader/writer): ").strip().lower()
    result = service.register_user({"username": username, "password": password, "role": role})
    print("  OK: " + result)


def op_login(service, session):
    username = input("  Uporabniško ime: ").strip()
    password = input("  Geslo: ").strip()
    session["header"] = make_header(session["client"], username, password)
    session["username"] = username
    print("  OK: prijavljen kot " + username + " (poverilnice se preverijo ob naslednjem klicu).")


def op_demo(service, session):
    if not require_login(session):
        return
    h = [session["header"]]
    username = session["username"]
    serial = "PDU-2026-0001"
    print("  Demo: kličem vse operacije kot " + username + " ...")

    print("  [1] register_user z zasedenim imenom '" + username + "' (pričakujem napako) ...")
    try:
        service.register_user({"username": username, "password": "geslo123", "role": "reader"})
        print("    presenetljivo OK")
    except Fault as error:
        print("    SOAP napaka (pričakovano): " + str(error.message))

    print("  [2] get_device_states() ...")
    devices = service.get_device_states(_soapheaders=h)
    print("    OK: " + str(len(devices)) + " naprav")

    print("  [3] get_sensors(" + serial + ") ...")
    sensors = service.get_sensors(serial, _soapheaders=h)
    print("    OK: " + str(len(sensors)) + " senzorjev")

    print("  [4] get_readings(" + serial + ") ...")
    readings = service.get_readings(serial, _soapheaders=h)
    print("    OK: " + str(len(readings)) + " meritve")

    print("  [5] set_device_state(" + serial + ", 'BLA') (pričakujem napako) ...")
    try:
        service.set_device_state(serial, "BLA", _soapheaders=h)
        print("    presenetljivo OK")
    except Fault as error:
        print("    SOAP napaka (pričakovano): " + str(error.message))

    print("  [6] set_device_state(" + serial + ", 'OFF') ...")
    try:
        service.set_device_state(serial, "OFF", _soapheaders=h)
        print("    OK: ukaz poslan (one-way, brez odziva)")
    except Fault as error:
        print("    SOAP napaka: " + str(error.message))


def main():
    print("Povezujem se na " + WSDL + " ...")
    try:
        client = Client(WSDL)
    except TransportError as error:
        print("Napaka pri povezavi: " + str(error))
        print("Preveri, ali strežnik teče (python run_server.py).")
        return

    service = client.service
    print("Povezano.")

    session = {"client": client, "header": None, "username": None}

    handlers = {
        "1": op_states,
        "2": op_set_state,
        "3": op_sensors,
        "4": op_readings,
        "5": op_register,
        "6": op_login,
        "7": op_demo,
    }

    while True:
        print_menu(session)
        try:
            choice = input("Izberi: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("Prekinjeno.")
            break

        if choice == "0":
            print("Nasvidenje.")
            break

        handler = handlers.get(choice)
        if handler is None:
            print("Neveljavna izbira.")
            continue

        try:
            handler(service, session)
        except Fault as error:
            print("  SOAP napaka: " + str(error.message))
        except TransportError as error:
            print("  Napaka povezave: " + str(error))
        except ValueError:
            print("  Neveljaven vnos (pričakovano število).")
        except (EOFError, KeyboardInterrupt):
            print()
            print("Prekinjeno.")
            break
        except Exception as error:
            print("  Nepričakovana napaka: " + str(error))


if __name__ == "__main__":
    main()
