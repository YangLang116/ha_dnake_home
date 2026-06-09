import logging

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.dnake_home.core.utils import get_key_by_value
from .core.assistant import assistant
from .core.constant import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)

_FRESH_AIR_MODES = {0: "低速", 1: "中速", 2: "高速", 3: "强劲"}

_MODE_PERCENTAGE = {0: 25, 1: 50, 2: 75, 3: 100}


def load_fans(device_list):
    fans = [
        DnakeFreshAir(device) for device in device_list if device.get("ty") == 16924
    ]
    _LOGGER.info(f"find fresh air fan num: {len(fans)}")
    assistant.entries["fan"] = fans


def update_fans_state(states):
    fans = assistant.entries["fan"]
    for fan in fans:
        state = next((state for state in states if state.get('devType') == 16924 and fan.is_hint_state(state)), None)
        if state:
            fan.update_state(state)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
):
    fan_list = assistant.entries["fan"]
    if fan_list:
        async_add_entities(fan_list)


class DnakeFreshAir(FanEntity):

    def __init__(self, device):
        self._name = device.get("na")
        self._dev_no = device.get("nm")
        self._dev_ch = device.get("ch")
        self._is_on = device.get("powerOn", 0) == 1
        self._mode = device.get("speed", 0)

    def is_hint_state(self, state):
        return state.get("devNo") == self._dev_no and state.get("devCh") == self._dev_ch

    @property
    def unique_id(self):
        return f"dnake_fresh_air_{self._dev_no}_{self._dev_ch}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"fresh_air_{self._dev_no}_{self._dev_ch}")},
            name=self._name,
            manufacturer=MANUFACTURER,
            model="新风系统",
            via_device=(DOMAIN, "gateway"),
        )

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on

    @property
    def percentage(self):
        return _MODE_PERCENTAGE.get(self._mode, 25)

    @property
    def speed_count(self):
        return len(_FRESH_AIR_MODES)

    @property
    def supported_features(self):
        return (
                FanEntityFeature.TURN_ON
                | FanEntityFeature.TURN_OFF
                | FanEntityFeature.SET_SPEED
                | FanEntityFeature.PRESET_MODE
        )

    @property
    def preset_mode(self):
        return _FRESH_AIR_MODES.get(self._mode, "低速")

    @property
    def preset_modes(self):
        return list(_FRESH_AIR_MODES.values())

    async def _set_power(self, is_on: bool):
        is_success = await self.hass.async_add_executor_job(
            assistant.set_fresh_air_power,
            self._dev_no,
            self._dev_ch,
            is_on,
        )
        if is_success:
            self._is_on = is_on
            self.async_write_ha_state()

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs):
        await self._set_power(True)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs):
        await self._set_power(False)

    async def async_set_percentage(self, percentage):
        if percentage <= 25:
            mode = 0
        elif percentage <= 50:
            mode = 1
        elif percentage <= 75:
            mode = 2
        else:
            mode = 3

        await self._set_mode(mode)

    async def async_set_preset_mode(self, preset_mode):
        await self._set_mode(get_key_by_value(_FRESH_AIR_MODES, preset_mode, 0))

    async def _set_mode(self, mode):
        is_success = await self.hass.async_add_executor_job(
            assistant.set_fresh_air_speed,
            self._dev_no,
            self._dev_ch,
            mode,
        )
        if is_success:
            self._mode = mode
            self.async_write_ha_state()

    def update_state(self, state):
        self._is_on = state.get("powerOn", 0) == 1
        self._mode = state.get("speed", 0)
        self.async_write_ha_state()
