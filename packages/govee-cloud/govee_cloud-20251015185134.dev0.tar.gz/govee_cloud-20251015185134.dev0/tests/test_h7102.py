import json
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from aioresponses import aioresponses

from devices.fan.h7102 import H7102
from util.govee_api import GoveeAPI


class TestH7102(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api_key = "test-api-key"
        self.govee = GoveeAPI(self.api_key, ignore_request_id=True)
        self.device_id = "test-device-id"
        self.device = H7102(self.device_id)
        self.mock_aioresponse = aioresponses()
        self.mock_aioresponse.start()

        # Load test data from JSON file
        test_data_path = Path(__file__).parent / "test_data" / "h7102.json"
        with open(test_data_path, "r") as f:
            self.test_data = json.load(f)

    async def asyncTearDown(self):
        await self.govee.client.close()
        self.mock_aioresponse.stop()

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

    async def test_oscillation(self):
        mock_response_on = self.test_data["oscillation_on"]
        mock_response_off = self.test_data["oscillation_off"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_on,
        )
        await self.device.toggle_oscillation(self.govee, True)
        self.assertTrue(self.device.oscillation_toggle)

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_off,
        )
        await self.device.toggle_oscillation(self.govee, False)
        self.assertFalse(self.device.oscillation_toggle)

    async def test_work_mode(self):
        mock_response_custom = self.test_data["custom_work_mode"]
        mock_response_auto = self.test_data["auto_work_mode"]
        mock_response_sleep = self.test_data["sleep_work_mode"]
        mock_response_nature = self.test_data["nature_work_mode"]
        update = self.test_data["update"]
        mock_response_normal = self.test_data["normal_work_mode"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_custom,
        )
        await self.device.set_work_mode(self.govee, "Custom")
        self.assertEqual(self.device.work_mode, "Custom")

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_auto,
        )
        await self.device.set_work_mode(self.govee, "Auto")
        self.assertEqual(self.device.work_mode, "Auto")

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
            payload=mock_response_nature,
        )
        await self.device.set_work_mode(self.govee, "Nature")
        self.assertEqual(self.device.work_mode, "Nature")

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/state",
            status=200,
            payload=update,
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_normal,
        )
        await self.device.update(self.govee)
        self.assertEqual(self.device.fan_speed, 2)

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/state",
            status=200,
            payload=update,
        )

        await self.device.set_work_mode(self.govee, "Normal")
        self.assertEqual(self.device.work_mode, "Normal")
        self.assertEqual(self.device.fan_speed, 1)

        with self.assertRaises(ValueError):
            await self.device.set_work_mode(self.govee, "Invalid")

    async def test_fan_speed(self):
        mock_response = self.test_data["fan_speed"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response,
        )
        await self.device.set_fan_speed(self.govee, 2)
        self.assertEqual(self.device.fan_speed, 2)

        with self.assertRaises(ValueError):
            await self.device.set_fan_speed(self.govee, 0)
        with self.assertRaises(ValueError):
            await self.device.set_fan_speed(self.govee, 9)

    async def test_update(self):
        mock_response = self.test_data["update"]

        with patch("devices.fan.h7102.logger.warning") as mock_logging:
            self.mock_aioresponse.post(
                "https://openapi.api.govee.com/router/api/v1/device/state",
                status=200,
                payload=mock_response,
            )
            await self.device.update(self.govee)
            self.assertEqual(self.device.online, True)
            self.assertEqual(self.device.power_switch, False)
            self.assertEqual(self.device.oscillation_toggle, False)
            self.assertEqual(self.device.work_mode, "Normal")
            self.assertEqual(self.device.fan_speed, 2)
            mock_logging.assert_called_once_with(
                "Found unknown capability type devices.capabilities.unknown"
            )

        with patch(
            "devices.fan.h7102.GoveeAPI.get_device_state"
        ) as mock_get_device_state:
            mock_get_device_state.side_effect = Exception("Test exception")
            await self.device.update(self.govee)
            self.assertEqual(self.device.online, False)

    async def test_str(self):
        expected_device_str = "Name: Smart Tower Fan, SKU: H7102, Device ID: test-device-id, Online: False, Power Switch: False, Oscillation Toggle: False, Work Mode: Normal, Fan Speed: 1"
        device_str = self.device.__str__()
        assert device_str == expected_device_str

    async def test_invalid_capability(self):
        capability = {
            "type": "devices.capabilities.unknown",
            "instance": "workMode",
            "state": {"status": "success"},
            "value": {"workMode": 2, "modeValue": 0},
        }

        with patch("devices.fan.h7102.logger.warning") as mock_logging:
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

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control", status=429
        )

        await self.device.toggle_oscillation(self.govee, True)
        self.assertEqual(self.device.online, False)

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control", status=429
        )

        await self.device.set_fan_speed(self.govee, 1)
        self.assertEqual(self.device.online, False)
