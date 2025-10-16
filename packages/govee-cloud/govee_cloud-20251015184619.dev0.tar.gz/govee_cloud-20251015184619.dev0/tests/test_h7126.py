import json
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from aioresponses import aioresponses

from devices.air_purifier.h7126 import H7126
from util.govee_api import GoveeAPI
from util.govee_appliance_api import GoveeApplianceAPI


class TestH7126(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api_key = "test-api-key"
        self.govee = GoveeAPI(self.api_key, ignore_request_id=True)
        self.govee_appliance = GoveeApplianceAPI(self.api_key)
        self.device_id = "test-device-id"
        self.device = H7126(self.device_id)
        self.mock_aioresponse = aioresponses()
        self.mock_aioresponse.start()

        # Load test data from JSON file
        test_data_path = Path(__file__).parent / "test_data" / "h7126.json"
        with open(test_data_path, "r") as f:
            self.test_data = json.load(f)

    async def asyncTearDown(self):
        await self.govee.client.close()
        self.mock_aioresponse.stop()

    async def test_update(self):
        mock_response = self.test_data["update"]
        mock_response_custom = self.test_data["update_custom_work_mode"]

        with patch("devices.air_purifier.h7126.logger.warning") as mock_logging:
            self.mock_aioresponse.post(
                "https://openapi.api.govee.com/router/api/v1/device/state",
                status=200,
                payload=mock_response,
            )
            await self.device.update(self.govee)
            self.assertEqual(self.device.online, True)
            self.assertEqual(self.device.power_switch, True)
            self.assertEqual(self.device.work_mode, "Low")
            self.assertEqual(self.device.filter_life, 0)
            self.assertEqual(self.device.air_quality, 6)

            # Check that each warning was called exactly once
            mock_logging.assert_any_call(
                "Found unknown capability type devices.capabilities.unknown"
            )
            mock_logging.assert_any_call("Found unknown instance unknown")

            # Verify there were exactly 2 calls
            self.assertEqual(mock_logging.call_count, 2)

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/state",
            status=200,
            payload=mock_response_custom,
        )
        await self.device.update(self.govee)
        self.assertEqual(self.device.online, True)
        self.assertEqual(self.device.power_switch, True)
        self.assertEqual(self.device.work_mode, "Custom")
        self.assertEqual(self.device.filter_life, 0)
        self.assertEqual(self.device.air_quality, 6)

        with patch(
            "devices.air_purifier.h7126.GoveeAPI.get_device_state"
        ) as mock_get_device_state:
            mock_get_device_state.side_effect = Exception("Test exception")
            await self.device.update(self.govee)
            self.assertEqual(self.device.online, False)

    async def test_str(self):
        expected_device_str = "Name: Smart Air Purifier, SKU: H7126, Device ID: test-device-id, Online: False, Power Switch: False, Work Mode: Sleep, Filter Life: 0, Air Quality: 0"
        device_str = self.device.__str__()
        assert device_str == expected_device_str

    async def test_power_switch(self):
        mock_response_on = self.test_data["power_switch_on"]
        mock_response_off = self.test_data["power_switch_off"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_on,
        )
        await self.device.turn_on(self.govee)
        self.assertTrue(self.device.power_switch)

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_off,
        )
        await self.device.turn_off(self.govee)
        self.assertFalse(self.device.power_switch)

    async def test_work_mode(self):
        mock_response_sleep = self.test_data["sleep_work_mode"]
        mock_response_low = self.test_data["low_work_mode"]
        mock_response_high = self.test_data["high_work_mode"]
        mock_response_custom = self.test_data["custom_work_mode"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_sleep,
        )
        await self.device.set_work_mode(self.govee, "Sleep")
        self.assertEqual(self.device.work_mode, "Sleep")

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_low,
        )
        await self.device.set_work_mode(self.govee, "Low")
        self.assertEqual(self.device.work_mode, "Low")

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_high,
        )
        await self.device.set_work_mode(self.govee, "High")
        self.assertEqual(self.device.work_mode, "High")

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_custom,
        )
        await self.device.set_work_mode(self.govee, "Custom")
        self.assertEqual(self.device.work_mode, "Custom")

        with self.assertRaises(ValueError):
            await self.device.set_work_mode(self.govee, "Invalid")

    async def test_invalid_capability(self):
        capability = {
            "type": "devices.capabilities.unknown",
            "instance": "workMode",
            "state": {"status": "success"},
            "value": {"workMode": 2, "modeValue": 0},
        }

        with patch("devices.air_purifier.h7126.logger.warning") as mock_logging:
            self.device.parse_response(capability)
            mock_logging.assert_called_once_with(
                "Found unknown capability type devices.capabilities.unknown"
            )

    async def test_rate_limit(self):
        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/state",
            status=429,
        )
        await self.device.update(self.govee)
        self.assertEqual(self.device.online, False)

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control", status=429
        )

        await self.device.turn_on(self.govee)
        self.assertEqual(self.device.online, False)

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control", status=429
        )

        await self.device.turn_off(self.govee)
        self.assertEqual(self.device.online, False)

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control", status=429
        )

        await self.device.set_work_mode(self.govee, "Sleep")
        self.assertEqual(self.device.online, False)
