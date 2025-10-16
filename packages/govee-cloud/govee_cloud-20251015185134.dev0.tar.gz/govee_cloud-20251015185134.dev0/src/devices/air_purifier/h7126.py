"""Smart Air Purifier"""

import logging

from devices.device_type import DeviceType
from devices.types.air_purifier import AirPurifier
from util.govee_api import GoveeAPI

logger = logging.getLogger("govee-cloud")


class H7126(AirPurifier):
    def __init__(self, device_id: str):
        work_modes: dict = {
            1: "Sleep",
            2: "Low",
            3: "High",
            4: "Custom",
        }
        sku: str = "H7126"
        device_name: str = "Smart Air Purifier"
        super().__init__(sku, device_id, device_name, work_modes)
        self.device_type: DeviceType = DeviceType.AIR_PURIFIER

    def __str__(self):
        return f"Name: {self.device_name}, SKU: {self.sku}, Device ID: {self.device_id}, Online: {self.online}, Power Switch: {self.power_switch}, Work Mode: {self.work_mode}, Filter Life: {self.filter_life}, Air Quality: {self.air_quality}"

    async def update(self, api: GoveeAPI):
        """
        Update the device state
        :param api: The Govee API
        """
        try:
            state = await api.get_device_state(self.sku, self.device_id)
            capabilities: dict = state["capabilities"]
            super().update(capabilities)
        except Exception as e:
            self.online = False
            logger.error(f"Error updating device state: {e}")
