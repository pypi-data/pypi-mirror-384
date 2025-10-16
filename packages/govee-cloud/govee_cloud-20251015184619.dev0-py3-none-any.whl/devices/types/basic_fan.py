import logging

from util.govee_api import GoveeAPI

logger = logging.getLogger("govee-cloud")


class BasicFan:
    def __init__(self, sku: str, device_id: str, device_name: str, work_modes: dict):
        self.work_modes: dict = work_modes
        self.sku: str = sku
        self.device_id: str = device_id
        self.device_name: str = device_name
        self.online: bool = False
        self.power_switch: bool = False
        self.work_mode: str = self.work_modes[1]
        self.speed_work_mode: str = "Custom"

    def update(self, capability: dict):
        capability_type: str = capability["type"]
        if capability_type == "devices.capabilities.online":
            self.online = capability["state"]["value"]
        elif capability_type == "devices.capabilities.on_off":
            self.power_switch = capability["state"]["value"] == 1
        else:
            logger.warning(f"Found unknown capability type {capability_type}")

    def parse_response(self, response: dict):
        capability_type: str = response["type"]
        if capability_type == "devices.capabilities.on_off":
            self.power_switch = response["value"] == 1
        elif capability_type == "devices.capabilities.work_mode":
            if response["value"]["workMode"] == 2:
                self.work_mode = "Custom"
            else:
                self.work_mode = self.work_modes[response["value"]["modeValue"]]
        else:
            logger.warning(f"Found unknown capability type {capability_type}")

    async def turn_on(self, api: GoveeAPI):
        """
        Turn on the device
        :param api: The Govee API
        """
        capability = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "value": 1,
        }
        try:
            response = await api.control_device(self.sku, self.device_id, capability)
            self.parse_response(response)
        except Exception as e:
            self.online = False
            logger.error(f"Error turning on device: {e}")

    async def turn_off(self, api: GoveeAPI):
        """
        Turn off the device
        :param api: The Govee API
        """
        capability = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "value": 0,
        }
        try:
            response = await api.control_device(self.sku, self.device_id, capability)
            self.parse_response(response)
        except Exception as e:
            self.online = False
            logger.error(f"Error turning off device: {e}")

    async def set_work_mode(self, api: GoveeAPI, work_mode: str):
        """
        Set the work mode of the device
        :param api: The Govee API
        :param work_mode: The work mode to set, must be in self.work_mode_dict.values()
        """
        if work_mode not in self.work_modes.values():
            raise ValueError(f"Invalid work mode {work_mode}")

        if work_mode == self.speed_work_mode:
            value = {"workMode": 2, "modeValue": 0}
        else:
            work_mode_key = None
            for key, value in self.work_modes.items():
                if value == work_mode:
                    work_mode_key = key

            value = {"workMode": 1, "modeValue": work_mode_key}

        capability = {
            "type": "devices.capabilities.work_mode",
            "instance": "workMode",
            "value": value,
        }
        try:
            response = await api.control_device(self.sku, self.device_id, capability)
            self.parse_response(response)
        except Exception as e:
            self.online = False
            logger.error(f"Error setting work mode: {e}")
