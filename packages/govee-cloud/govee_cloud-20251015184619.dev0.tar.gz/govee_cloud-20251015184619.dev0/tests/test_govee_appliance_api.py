import json
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from aioresponses import aioresponses

from util.govee_appliance_api import GoveeApplianceAPI


class TestGoveeApplianceAPI(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api_key = "test-api-key"
        self.govee = GoveeApplianceAPI(self.api_key)
        self.mock_aioresponse = aioresponses()
        self.mock_aioresponse.start()

        # Load test data from JSON file
        test_data_path = (
            Path(__file__).parent / "test_data" / "govee_appliance_api.json"
        )
        with open(test_data_path, "r") as f:
            self.test_data = json.load(f)

    async def asyncTearDown(self):
        await self.govee.client.close()
        self.mock_aioresponse.stop()

    async def test_control_devices(self):
        model = "H7102"
        device = "18:43:D4:AD:FC:XX:XX:XX"

        # Mock the response
        mock_response = self.test_data["control_device"]

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        mode_cmd = {"name": "mode", "value": 1}
        turn_cmd = {"name": "turn", "value": "on"}
        gear_cmd = {"name": "gear", "value": 3}
        invalid_cmd = {"name": "invalid", "value": 1}
        invalid_turn_cmd = {"name": "turn", "value": "invalid"}
        invalid_mode_cmd = {"name": "mode", "value": "invalid"}

        result = await self.govee.control_device(model, device, mode_cmd)

        self.assertEqual(result, mock_response["data"])

        mock_response = self.test_data["control_device_2"]

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        result = await self.govee.control_device(model, device, mode_cmd)

        self.assertEqual(result, mock_response["data"])

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        result = await self.govee.control_device(model, device, turn_cmd)

        self.assertEqual(result, mock_response["data"])

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        result = await self.govee.control_device(model, device, gear_cmd)

        self.assertEqual(result, mock_response["data"])

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(model, device, invalid_cmd)

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(model, device, invalid_turn_cmd)

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(model, device, invalid_mode_cmd)

    async def test_bad_response(self):
        model = "H7102"
        device = "18:43:D4:AD:FC:XX:XX:XX"

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control", status=400
        )

        with self.assertRaises(RuntimeError):
            await self.govee.control_device(model, device, {"name": "mode", "value": 1})

        mock_response = self.test_data["bad_request"]

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.control_device(model, device, {"name": "mode", "value": 1})

        mock_response = self.test_data["bad_request_2"]

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.control_device(model, device, {"name": "mode", "value": 1})

        mock_response = self.test_data["bad_request_3"]

        self.mock_aioresponse.put(
            "https://developer-api.govee.com/v1/appliance/devices/control",
            payload=mock_response,
            status=200,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.control_device(model, device, {"name": "mode", "value": 1})
