from spyne import ComplexModel, Unicode, DateTime, Array

class Sensor(ComplexModel):
    serial = Unicode
    name   = Unicode
    unit   = Unicode

class Device(ComplexModel):
    serial       = Unicode
    name         = Unicode
    manufacturer = Unicode
    state        = Unicode(pattern='^(ON|OFF)$')
    sensors      = Array(Sensor)   

class Reading(ComplexModel):
    sensor_serial = Unicode
    timestamp     = DateTime       
    value         = Unicode        