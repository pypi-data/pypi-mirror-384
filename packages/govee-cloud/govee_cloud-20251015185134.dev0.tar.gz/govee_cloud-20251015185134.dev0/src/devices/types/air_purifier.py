import logging

from devices.types.basic_fan import BasicFan

logger = logging.getLogger("govee-cloud")


class AirPurifier(BasicFan):
    def __init__(self, sku: str, device_id: str, device_name: str, work_modes: dict):
        super().__init__(sku, device_id, device_name, work_modes)
        self.filter_life: int = 0
        self.air_quality: int = 0

    def update(self, capabilities: dict):
        for capability in capabilities:
            capability_type: str = capability["type"]
            if capability_type == "devices.capabilities.property":
                instance = capability["instance"]
                if instance == "filterLifeTime":
                    self.filter_life = capability["state"]["value"]
                elif instance == "airQuality":
                    self.air_quality = capability["state"]["value"]
                else:
                    logger.warning(f"Found unknown instance {instance}")
                    continue
            elif capability_type == "devices.capabilities.work_mode":
                if capability["state"]["value"]["workMode"] == 2:
                    self.work_mode = "Custom"
                else:
                    self.work_mode = self.work_modes[
                        capability["state"]["value"]["modeValue"]
                    ]
            else:
                super().update(capability)
