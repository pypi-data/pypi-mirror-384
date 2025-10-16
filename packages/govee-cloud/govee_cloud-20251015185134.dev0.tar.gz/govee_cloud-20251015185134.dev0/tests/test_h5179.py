import json
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from aioresponses import aioresponses

from devices.thermometer.h5179 import H5179
from util.govee_api import GoveeAPI
from util.govee_appliance_api import GoveeApplianceAPI


class TestH5179(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api_key = "test-api-key"
        self.govee = GoveeAPI(self.api_key, ignore_request_id=True)
        self.govee_appliance = GoveeApplianceAPI(self.api_key)
        self.device_id = "test-device-id"
        self.device = H5179(self.device_id)
        self.mock_aioresponse = aioresponses()
        self.mock_aioresponse.start()

        # Load test data from JSON file
        test_data_path = Path(__file__).parent / "test_data" / "h5179.json"
        with open(test_data_path, "r") as f:
            self.test_data = json.load(f)

    async def asyncTearDown(self):
        await self.govee.client.close()
        self.mock_aioresponse.stop()

    async def test_update(self):
        mock_response = self.test_data["update_response"]

        with patch("devices.thermometer.h5179.log.warning") as mock_logging:
            self.mock_aioresponse.post(
                "https://openapi.api.govee.com/router/api/v1/device/state",
                status=200,
                payload=mock_response,
            )
            await self.device.update(self.govee)
            self.assertEqual(self.device.online, True)
            self.assertEqual(self.device.temperature, 66.74)
            self.assertEqual(self.device.humidity, 50)

            # Check that each warning was called exactly once
            mock_logging.assert_any_call(
                "Found unknown capability type devices.capabilities.unknown"
            )
            mock_logging.assert_any_call("Found unknown instance unknown")

            # Verify there were exactly 2 calls
            self.assertEqual(mock_logging.call_count, 2)

        with patch(
            "devices.thermometer.h5179.GoveeAPI.get_device_state"
        ) as mock_get_device_state:
            mock_get_device_state.side_effect = Exception("Test exception")
            await self.device.update(self.govee)
            self.assertEqual(self.device.online, False)

    async def test_str(self):
        expected_device_str = "Name: Wi-Fi Thermometer, Device ID: test-device-id, Online: False, Temperature: 0.0F, Humidity: 0.0%"
        device_str = self.device.__str__()
        assert device_str == expected_device_str

    async def test_rate_limit(self):
        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/state",
            status=429,
        )
        await self.device.update(self.govee)
        self.assertEqual(self.device.online, False)
