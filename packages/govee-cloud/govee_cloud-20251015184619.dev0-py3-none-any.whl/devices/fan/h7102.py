"""Smart Tower Fan"""

import logging
from devices.device_type import DeviceType
from devices.types.fan import Fan
from util.govee_api import GoveeAPI

logger = logging.getLogger("govee-cloud")


class H7102(Fan):
    def __init__(self, device_id: str):
        work_modes = {
            1: "Normal",
            2: "Custom",
            3: "Auto",
            5: "Sleep",
            6: "Nature",
        }
        sku: str = "H7102"
        device_name: str = "Smart Tower Fan"
        super().__init__(sku, device_id, device_name, work_modes, 1, 8)
        self.device_type: DeviceType = DeviceType.FAN

    def __str__(self):
        return f"Name: {self.device_name}, SKU: {self.sku}, Device ID: {self.device_id}, Online: {self.online}, Power Switch: {self.power_switch}, Oscillation Toggle: {self.oscillation_toggle}, Work Mode: {self.work_mode}, Fan Speed: {self.fan_speed}"

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
