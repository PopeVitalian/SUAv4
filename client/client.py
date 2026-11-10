#!/usr/bin/env python3
# console client, prej zaženi run_server.py

from zeep import Client
from zeep.exceptions import Fault, TransportError


WSDL = "http://127.0.0.1:8007/?wsdl"


def print_menu():
    print()
    print("=== Server Room SOAP Client ===")
    print("1) Prikaži stanja vseh naprav")
    print("2) Nastavi stanje naprave (ON/OFF)")
    print("3) Prikaži senzorje naprave")
    print("4) Prikaži meritve naprave")
    print("5) Preklopi vtičnico PDU (1-8)")
    print("6) Nastavi alarmno temperaturo ENV")
    print("7) Nastavi PTZ pozicijo CAM")
    print("0) Izhod")


def op_states(service):
    devices = service.get_device_states()
    print()
    for device in devices:
        print("  " + device["serial"] + "  " + device["name"] + "  stanje=" + str(device["state"]))


def op_set_state(service):
    serial = input("  Serijska številka naprave: ").strip()
    state = input("  Novo stanje (ON/OFF): ").strip().upper()
    device = service.set_device_state(serial, state)
    print("  OK: " + device["serial"] + " -> " + str(device["state"]))


def op_sensors(service):
    serial = input("  Serijska številka naprave: ").strip()
    sensors = service.get_sensors(serial)
    print()
    for sensor in sensors:
        print("    - " + sensor["serial"] + "  (" + sensor["name"] + ", enota=" + sensor["unit"] + ")")


def op_readings(service):
    serial = input("  Serijska številka naprave: ").strip()
    readings = service.get_readings(serial)
    print()
    for reading in readings:
        print("    - " + reading["sensor_serial"] + " @ " + str(reading["timestamp"]) + " -> " + str(reading["value"]))


def op_toggle_outlet(service):
    serial = input("  Serijska številka PDU (npr. PDU-2026-0001): ").strip()
    index_str = input("  Indeks vtičnice (1-8): ").strip()
    index = int(index_str)
    device = service.toggle_outlet(serial, index)
    print("  OK: preklopljena vtičnica " + str(index) + " na " + device["serial"])


def op_set_alarm(service):
    serial = input("  Serijska številka ENV (npr. ENV-2026-0001): ").strip()
    temp_str = input("  Alarmna temperatura v C: ").strip()
    temp = float(temp_str)
    device = service.set_alarm_temp(serial, temp)
    print("  OK: alarm nastavljen na " + device["serial"])


def op_goto_preset(service):
    serial = input("  Serijska številka CAM (npr. CAM-2026-0001): ").strip()
    preset = input("  Pozicija (door / aisle-a / rack-3): ").strip()
    device = service.goto_preset(serial, preset)
    print("  OK: pozicija nastavljena na " + device["serial"])


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

    handlers = {
        "1": op_states,
        "2": op_set_state,
        "3": op_sensors,
        "4": op_readings,
        "5": op_toggle_outlet,
        "6": op_set_alarm,
        "7": op_goto_preset,
    }

    while True:
        print_menu()
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
            handler(service)
        except Fault as error:
            print("  SOAP napaka: " + str(error.message))
        except ValueError:
            print("  Neveljaven vnos (pričakovano število).")
        except (EOFError, KeyboardInterrupt):
            print()
            print("Prekinjeno.")
            break


if __name__ == "__main__":
    main()