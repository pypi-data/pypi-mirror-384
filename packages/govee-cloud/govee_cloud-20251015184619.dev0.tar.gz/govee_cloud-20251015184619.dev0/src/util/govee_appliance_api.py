import logging

import aiohttp

from util import on_request_start, on_request_end

logger = logging.getLogger("govee-cloud")


cmds = ["mode", "turn", "gear"]


async def validate_response(response: aiohttp.ClientResponse):
    if response.status != 200:
        raise RuntimeError(
            f"Request failed with status code {response.status} and message {response.reason}"
        )
    response: dict = await response.json()
    if "code" in response:
        if response["code"] != 200 and response["message"] != "Success":
            logger.error(
                "Request failed with error code %s and message %s",
                response["code"],
                response["message"],
            )
            raise RuntimeError(
                f"Request failed with error code {response['code']} and message {response['message']}"
            )
    elif "status" in response:
        if response["status"] != 200 and response["message"] != "Success":
            logger.error(
                "Request failed with error code %s and message %s",
                response["status"],
                response["message"],
            )
            raise RuntimeError(
                f"Request failed with error code {response['status']} and message {response['message']}"
            )
    else:
        logger.error("Request failed with error code %s", response)
        raise RuntimeError(f"Request failed with error code {response}")


def validate_cmd(cmd: dict) -> bool:
    if cmd["name"] not in cmds:
        logger.error("Command %s is not supported", cmd["name"])
        raise ValueError(f"Command {cmd['name']} is not supported")
    if cmd["name"] == "turn" and cmd["value"] not in ["on", "off"]:
        logger.error("Value %s is not supported for command 'turn'", cmd["value"])
        raise ValueError("Value must be `on` or `off` for command 'turn'")
    if (cmd["name"] == "mode" or cmd["name"] == "gear") and type(
        cmd["value"]
    ) is not int:
        logger.error(
            "Value %s is not supported for command 'mode' or 'gear'", cmd["value"]
        )
        raise ValueError("Value must be an integer for command 'mode' or 'gear'")
    return True


class GoveeApplianceAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://developer-api.govee.com"
        self.headers = {
            "Govee-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)
        self.client = aiohttp.ClientSession(
            base_url=self.base_url,
            headers=self.headers,
            raise_for_status=validate_response,
            trace_configs=[trace_config],
        )

    async def control_device(self, model: str, device: str, cmd: dict) -> dict | None:
        """
        Control an appliance device
        :param model: The model of the appliance to control
        :param device: The device ID of the appliance to control
        :param cmd: The command to send to the appliance
        :return: The data response from the API
        """
        body = {"device": device, "model": model, "cmd": cmd}
        validate_cmd(cmd)
        async with self.client.put(
            "/v1/appliance/devices/control", json=body
        ) as response:
            json = await response.json()
            return json["data"]
