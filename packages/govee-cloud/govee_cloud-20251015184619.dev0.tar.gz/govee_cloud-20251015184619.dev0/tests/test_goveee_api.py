import json
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from aioresponses import aioresponses

from src.util.govee_api import GoveeAPI


class TestGoveeAPI(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api_key = "test-api-key"
        self.govee = GoveeAPI(self.api_key)
        self.mock_aioresponse = aioresponses()
        self.mock_aioresponse.start()

        # Load test data from JSON file
        test_data_path = Path(__file__).parent / "test_data" / "govee_api.json"
        with open(test_data_path, "r") as f:
            self.test_data = json.load(f)

    async def asyncTearDown(self):
        await self.govee.client.close()
        self.mock_aioresponse.stop()

    async def test_get_devices(self):
        # Get response data from the loaded test data
        mock_response = self.test_data["get_devices"]

        # Mock the GET request
        self.mock_aioresponse.get(
            "https://openapi.api.govee.com/router/api/v1/user/devices",
            status=200,
            payload=mock_response,
        )

        # Call the method being tested
        result = await self.govee.get_devices()

        # Verify the results
        self.assertEqual(result, mock_response["data"])

    async def test_get_devices_bad_api_key(self):
        self.mock_aioresponse.get(
            "https://openapi.api.govee.com/router/api/v1/user/devices", status=401
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_devices()

    async def test_get_devices_rate_limited(self):
        self.mock_aioresponse.get(
            "https://openapi.api.govee.com/router/api/v1/user/devices", status=429
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_devices()

    async def test_get_device_state(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        mock_response = self.test_data["get_device_state"]

        # Mock the GET request
        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/state",
            status=200,
            payload=mock_response,
        )

        # Call the method being tested
        result = await self.govee.get_device_state(sku, device, request_id=uuid)

        # Verify the results
        self.assertEqual(result, mock_response["payload"])

    async def test_get_device_state_invalid_request_id(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "invalid-request-id"

        mock_response = self.test_data["get_device_state"]

        # Mock the GET request
        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/state",
            status=200,
            payload=mock_response,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_device_state(sku, device, request_id=uuid)

    async def test_get_device_state_bad_api_key(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/state", status=401
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_device_state(sku, device, request_id=uuid)

    async def test_get_device_state_rate_limited(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/state", status=429
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_device_state(sku, device, request_id=uuid)

    async def test_control_device_on_off(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        capability_off = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "value": 0,
        }

        capability_on = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "value": 1,
        }

        mock_response_off = self.test_data["control_device_off"]
        mock_response_on = self.test_data["control_device_on"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_off,
        )

        result_off = await self.govee.control_device(
            sku, device, capability_off, request_id=uuid
        )

        self.assertEqual(result_off, mock_response_off["capability"])

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_on,
        )

        result_on = await self.govee.control_device(
            sku, device, capability_on, request_id=uuid
        )

        self.assertEqual(result_on, mock_response_on["capability"])

    async def test_control_device_toggle(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        oscillation_toggle = {
            "type": "devices.capabilities.toggle",
            "instance": "oscillationToggle",
            "value": 0,
        }

        mock_oscillation_toggle = self.test_data["oscillation_toggle"]

        nightlight_toggle = {
            "type": "devices.capabilities.toggle",
            "instance": "nightlightToggle",
            "value": 0,
        }

        mock_nightlight_toggle = self.test_data["nightlight_toggle"]

        air_deflector_toggle = {
            "type": "devices.capabilities.toggle",
            "instance": "airDeflectorToggle",
            "value": 0,
        }

        mock_air_deflector_toggle = self.test_data["air_deflector_toggle"]

        gradient_toggle = {
            "type": "devices.capabilities.toggle",
            "instance": "gradientToggle",
            "value": 0,
        }

        mock_gradient_toggle = self.test_data["gradient_toggle"]

        thermostat_toggle = {
            "type": "devices.capabilities.toggle",
            "instance": "thermostatToggle",
            "value": 0,
        }

        mock_thermostat_toggle = self.test_data["thermostat_toggle"]

        warm_mist_toggle = {
            "type": "devices.capabilities.toggle",
            "instance": "warmMistToggle",
            "value": 0,
        }

        mock_warm_mist_toggle = self.test_data["warm_mist_toggle"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_oscillation_toggle,
        )

        result_oscillation_toggle = await self.govee.control_device(
            sku, device, oscillation_toggle, request_id=uuid
        )

        self.assertEqual(
            result_oscillation_toggle, mock_oscillation_toggle["capability"]
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_nightlight_toggle,
        )

        result_nightlight_togglee = await self.govee.control_device(
            sku, device, nightlight_toggle, request_id=uuid
        )

        self.assertEqual(
            result_nightlight_togglee, mock_nightlight_toggle["capability"]
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_air_deflector_toggle,
        )

        result_air_deflector_toggle = await self.govee.control_device(
            sku, device, air_deflector_toggle, request_id=uuid
        )

        self.assertEqual(
            result_air_deflector_toggle, mock_air_deflector_toggle["capability"]
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_gradient_toggle,
        )

        result_gradient_toggle = await self.govee.control_device(
            sku, device, gradient_toggle, request_id=uuid
        )

        self.assertEqual(result_gradient_toggle, mock_gradient_toggle["capability"])

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_thermostat_toggle,
        )

        result_thermostat_toggle = await self.govee.control_device(
            sku, device, thermostat_toggle, request_id=uuid
        )

        self.assertEqual(result_thermostat_toggle, mock_thermostat_toggle["capability"])

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_warm_mist_toggle,
        )

        result_warm_mist_toggle = await self.govee.control_device(
            sku, device, warm_mist_toggle, request_id=uuid
        )

        self.assertEqual(result_warm_mist_toggle, mock_warm_mist_toggle["capability"])

    async def test_control_device_color_setting(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        color_rgb_capability = {
            "type": "devices.capabilities.color_setting",
            "instance": "colorRgb",
            "value": 0,
        }

        mock_color_rgb_capability = self.test_data["color_rgb_capability"]

        color_temperature_k_capability = {
            "type": "devices.capabilities.color_setting",
            "instance": "colorTemperatureK",
            "value": 0,
        }

        mock_color_temperature_k_capability = self.test_data[
            "color_temperature_k_capability"
        ]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_color_rgb_capability,
        )

        result_color_rgb_capability = await self.govee.control_device(
            sku, device, color_rgb_capability, request_id=uuid
        )

        self.assertEqual(
            result_color_rgb_capability, mock_color_rgb_capability["capability"]
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_color_temperature_k_capability,
        )

        result_color_temperature_k_capability = await self.govee.control_device(
            sku, device, color_temperature_k_capability, request_id=uuid
        )

        self.assertEqual(
            result_color_temperature_k_capability,
            mock_color_temperature_k_capability["capability"],
        )

    async def test_control_device_mode(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        night_light_scene_capability = {
            "type": "devices.capabilities.mode",
            "instance": "nightlightScene",
            "value": 1,
        }

        mock_night_light_scene_capability = self.test_data[
            "night_light_scene_capability"
        ]

        preset_scene_capability = {
            "type": "devices.capabilities.mode",
            "instance": "presetScene",
            "value": 1,
        }

        mock_preset_scene_capability = self.test_data["preset_scene_capability"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_night_light_scene_capability,
        )

        result_night_light_scene_capability = await self.govee.control_device(
            sku, device, night_light_scene_capability, request_id=uuid
        )

        self.assertEqual(
            result_night_light_scene_capability,
            mock_night_light_scene_capability["capability"],
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_preset_scene_capability,
        )

        result_preset_scene_capability = await self.govee.control_device(
            sku, device, preset_scene_capability, request_id=uuid
        )

        self.assertEqual(
            result_preset_scene_capability, mock_preset_scene_capability["capability"]
        )

    async def test_control_device_range(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        brightness_capability = {
            "type": "devices.capabilities.range",
            "instance": "brightness",
            "value": 50,
        }

        mock_brightness_capability = self.test_data["brightness_capability"]

        humidity_capability = {
            "type": "devices.capabilities.range",
            "instance": "humidity",
            "value": 50,
        }

        mock_humidity_capability = self.test_data["humidity_capability"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_brightness_capability,
        )

        result_brightness_capability = await self.govee.control_device(
            sku, device, brightness_capability, request_id=uuid
        )

        self.assertEqual(
            result_brightness_capability, mock_brightness_capability["capability"]
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_humidity_capability,
        )

        result_humidity_capability = await self.govee.control_device(
            sku, device, humidity_capability, request_id=uuid
        )

        self.assertEqual(
            result_humidity_capability, mock_humidity_capability["capability"]
        )

    async def test_control_device_work_mode(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        work_mode_capability = {
            "type": "devices.capabilities.work_mode",
            "instance": "workMode",
            "value": {"workMode": 1, "modeValue": 1},
        }

        mock_work_mode_capability = self.test_data["work_mode_capability"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_work_mode_capability,
        )

        result_work_mode_capability = await self.govee.control_device(
            sku, device, work_mode_capability, request_id=uuid
        )

        self.assertEqual(
            result_work_mode_capability, mock_work_mode_capability["capability"]
        )

    async def test_control_segment_color_setting(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        segmented_color_rgb_capability = {
            "type": "devices.capabilities.segment_color_setting",
            "instance": "segmentedColorRgb",
            "value": {"segment": [0, 1, 2, 3, 4, 5, 6, 7, 8], "rgb": "0x0000ff"},
        }

        mock_segmented_color_rgb_capability = self.test_data[
            "segmented_color_rgb_capability"
        ]

        segmented_brightness_capability = {
            "type": "devices.capabilities.segment_color_setting",
            "instance": "segmentedBrightness",
            "value": {"segment": [0, 1, 2, 3, 4, 5, 6, 7, 8], "brightness": 50},
        }

        mock_segmented_brightness_capability = self.test_data[
            "segmented_brightness_capability"
        ]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_segmented_color_rgb_capability,
        )

        result_segmented_color_rgb_capability = await self.govee.control_device(
            sku, device, segmented_color_rgb_capability, request_id=uuid
        )

        self.assertEqual(
            result_segmented_color_rgb_capability,
            mock_segmented_color_rgb_capability["capability"],
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_segmented_brightness_capability,
        )

        result_segmented_brightness_capability = await self.govee.control_device(
            sku, device, segmented_brightness_capability, request_id=uuid
        )

        self.assertEqual(
            result_segmented_brightness_capability,
            mock_segmented_brightness_capability["capability"],
        )

    async def test_control_segment_dynamic_scene(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        light_scene_capability = {
            "type": "devices.capabilities.dynamic_scene",
            "instance": "lightScene",
            "value": 4,
        }

        mock_light_scene_capability = self.test_data["light_scene_capability"]

        diy_scene_capability = {
            "type": "devices.capabilities.dynamic_scene",
            "instance": "diyScene",
            "value": 4,
        }

        mock_diy_scene_capability = self.test_data["diy_scene_capability"]

        snapshot_capability = {
            "type": "devices.capabilities.dynamic_scene",
            "instance": "snapshot",
            "value": 4,
        }

        mock_snapshot_capability = self.test_data["snapshot_capability"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_light_scene_capability,
        )

        result_light_scene_capability = await self.govee.control_device(
            sku, device, light_scene_capability, request_id=uuid
        )

        self.assertEqual(
            result_light_scene_capability, mock_light_scene_capability["capability"]
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_diy_scene_capability,
        )

        result_diy_scene_capability = await self.govee.control_device(
            sku, device, diy_scene_capability, request_id=uuid
        )

        self.assertEqual(
            result_diy_scene_capability, mock_diy_scene_capability["capability"]
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_snapshot_capability,
        )

        result_snapshot_capability = await self.govee.control_device(
            sku, device, snapshot_capability, request_id=uuid
        )

        self.assertEqual(
            result_snapshot_capability, mock_snapshot_capability["capability"]
        )

    async def test_control_music_setting(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        music_mode_capability = {
            "type": "devices.capabilities.music_setting",
            "instance": "musicMode",
            "value": {"musicMode": 25, "sensitivity": 50},
        }

        mock_music_mode_capability = self.test_data["music_mode_capability"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_music_mode_capability,
        )

        result_music_mode_capability = await self.govee.control_device(
            sku, device, music_mode_capability, request_id=uuid
        )

        self.assertEqual(
            result_music_mode_capability, mock_music_mode_capability["capability"]
        )

    async def test_control_temperature_setting(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        target_temperature_capability = {
            "type": "devices.capabilities.temperature_setting",
            "instance": "targetTemperature",
            "value": {"temperature": 25, "unit": "Celsius"},
        }

        mock_target_temperature_capability = self.test_data[
            "target_temperature_capability"
        ]

        slider_temperature_capability = {
            "type": "devices.capabilities.temperature_setting",
            "instance": "sliderTemperature",
            "value": {"autoStop": 1, "temperature": 25, "unit": "Celsius"},
        }

        mock_slider_temperature_capability = self.test_data[
            "slider_temperature_capability"
        ]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_target_temperature_capability,
        )

        result_target_temperature_capability = await self.govee.control_device(
            sku, device, target_temperature_capability, request_id=uuid
        )

        self.assertEqual(
            result_target_temperature_capability,
            mock_target_temperature_capability["capability"],
        )

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_slider_temperature_capability,
        )

        result_slider_temperature_capability = await self.govee.control_device(
            sku, device, slider_temperature_capability, request_id=uuid
        )

        self.assertEqual(
            result_slider_temperature_capability,
            mock_slider_temperature_capability["capability"],
        )

    async def test_control_device_invalid_capability(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        empty_capability = {}

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=empty_capability,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(
                sku, device, empty_capability, request_id=uuid
            )

        invalid_type_capability = {"type": 123}

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=invalid_type_capability,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(
                sku, device, invalid_type_capability, request_id=uuid
            )

        no_instance_capability = {"type": "devices.capabilities.on_off"}

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=no_instance_capability,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(
                sku, device, no_instance_capability, request_id=uuid
            )

        invalid_instance_capability = {
            "type": "devices.capabilities.on_off",
            "instance": 123,
        }

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=invalid_instance_capability,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(
                sku, device, invalid_instance_capability, request_id=uuid
            )

        no_value_capability = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
        }

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=no_value_capability,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(
                sku, device, no_value_capability, request_id=uuid
            )

        invalid_value_capability = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "value": "invalid-value",
        }

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=invalid_value_capability,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(
                sku, device, invalid_value_capability, request_id=uuid
            )

        invalid_capability_type = {
            "type": "devices.capabilities.test",
            "instance": "powerSwitch",
            "value": 0,
        }

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=invalid_capability_type,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(
                sku, device, invalid_capability_type, request_id=uuid
            )

        invalid_instance_type = {
            "type": "devices.capabilities.on_off",
            "instance": "test",
            "value": 0,
        }

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=invalid_instance_type,
        )

        with self.assertRaises(ValueError):
            await self.govee.control_device(
                sku, device, invalid_instance_type, request_id=uuid
            )

    async def test_control_device_bad_uuid(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"
        invalid_uuid = "invalid-request-id"

        capability_off = {
            "type": "devices.capabilities.on_off",
            "instance": "powerSwitch",
            "value": 0,
        }

        mock_response_off = self.test_data["control_device_off"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/control",
            status=200,
            payload=mock_response_off,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.control_device(
                sku, device, capability_off, request_id=invalid_uuid
            )

    async def test_get_dynamic_light_scene(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"

        invalid_uuid = "invalid-request-id"

        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        mock_response = self.test_data["get_dynamic_light_scene"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/scenes",
            status=200,
            payload=mock_response,
        )

        result = await self.govee.get_dynamic_light_scene(sku, device, request_id=uuid)

        self.assertEqual(result, mock_response["payload"])

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/scenes",
            status=200,
            payload=mock_response,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_dynamic_light_scene(
                sku, device, request_id=invalid_uuid
            )

    async def test_get_diy_scene(self):
        sku = "H7143"
        device = "52:8B:D4:AD:FC:45:5D:FE"

        invalid_uuid = "invalid-request-id"

        uuid = "98e662be-9837-439f-833e-83b5152142f5"

        mock_response = self.test_data["get_diy_scene"]

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/diy-scenes",
            status=200,
            payload=mock_response,
        )

        result = await self.govee.get_diy_scene(sku, device, request_id=uuid)

        self.assertEqual(result, mock_response["payload"])

        self.mock_aioresponse.post(
            "https://openapi.api.govee.com/router/api/v1/device/diy-scenes",
            status=200,
            payload=mock_response,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_diy_scene(sku, device, request_id=invalid_uuid)

    async def test_bad_api_response(self):
        response = {"code": 400}

        self.mock_aioresponse.get(
            "https://openapi.api.govee.com/router/api/v1/user/devices",
            status=200,
            payload=response,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_devices()

        response = {"code": 400, "message": "Missing Parameter"}

        self.mock_aioresponse.get(
            "https://openapi.api.govee.com/router/api/v1/user/devices",
            status=200,
            payload=response,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_devices()

        response = {"code": 400, "msg": "Missing Parameter"}

        self.mock_aioresponse.get(
            "https://openapi.api.govee.com/router/api/v1/user/devices",
            status=200,
            payload=response,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_devices()

        response = {"code": 200, "msg": "Success"}

        self.mock_aioresponse.get(
            "https://openapi.api.govee.com/router/api/v1/user/devices",
            status=200,
            payload=response,
        )

        with self.assertRaises(RuntimeError):
            await self.govee.get_devices()
