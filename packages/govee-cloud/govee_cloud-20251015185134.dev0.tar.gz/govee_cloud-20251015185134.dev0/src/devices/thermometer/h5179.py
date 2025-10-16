"""Wi-Fi Thermometer"""

import logging

from devices.device_type import DeviceType
from devices.types.thermometer import Thermometer
from util.govee_api import GoveeAPI

log = logging.getLogger("govee-cloud")


class H5179(Thermometer):
    def __init__(self, device_id: str):
        sku: str = "H5179"
        device_name: str = "Wi-Fi Thermometer"
        super().__init__(sku, device_id, device_name)
        self.device_type: DeviceType = DeviceType.THERMOMETER

    def __str__(self):
        return f"Name: {self.device_name}, Device ID: {self.device_id}, Online: {self.online}, Temperature: {self.temperature}F, Humidity: {self.humidity}%"

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
            log.error(f"Error updating device state: {e}")
