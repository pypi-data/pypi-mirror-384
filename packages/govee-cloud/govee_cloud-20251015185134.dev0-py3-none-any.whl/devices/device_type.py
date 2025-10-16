from enum import Enum


class DeviceType(Enum):
    LIGHT = "devices.types.light"
    AIR_PURIFIER = "devices.types.air_purifier"
    THERMOMETER = "devices.types.thermometer"
    SOCKET = "devices.types.socket"
    SENSOR = "devices.types.sensor"
    HEATER = "devices.types.heater"
    HUMIDIFIER = "devices.types.humidifier"
    DEHUMIDIFIER = "devices.types.dehumidifier"
    ICE_MAKER = "devices.types.ice_maker"
    AROMA_DIFFUSER = "devices.types.aroma_diffuser"
    BOX = "devices.types.box"
    FAN = "devices.types.fan"
