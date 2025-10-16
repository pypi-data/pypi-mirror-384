import logging

logger = logging.getLogger("govee-cloud")


class Thermometer:
    def __init__(self, sku: str, device_id: str, device_name: str):
        self.sku: str = sku
        self.device_id: str = device_id
        self.device_name: str = device_name
        self.online: bool = False
        self.temperature: float = 0.0
        self.humidity: float = 0.0

    def update(self, capabilities: dict):
        for capability in capabilities:
            capability_type: str = capability["type"]
            if capability_type == "devices.capabilities.online":
                self.online = capability["state"]["value"]
            elif capability_type == "devices.capabilities.property":
                instance = capability["instance"]
                if instance == "sensorTemperature":
                    self.temperature = capability["state"]["value"]
                elif instance == "sensorHumidity":
                    self.humidity = capability["state"]["value"]
                else:
                    logger.warning(f"Found unknown instance {instance}")
                    continue
            else:
                logger.warning(f"Found unknown capability type {capability_type}")
