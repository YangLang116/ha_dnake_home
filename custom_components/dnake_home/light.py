import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.light import (
    LightEntity,
    ColorMode,
)
from homeassistant.helpers.entity import DeviceInfo
from .core.assistant import assistant
from .core.constant import DOMAIN, MANUFACTURER


_LOGGER = logging.getLogger(__name__)


def load_lights(device_list):
    lights = [DnakeLight(device) for device in device_list if device.get("ty") == 256]
    _LOGGER.info(f"find light num: {len(lights)}")
    assistant.entries["light"] = lights


def update_lights_state(states):
    lights = assistant.entries["light"]
    for light in lights:
        state = next((state for state in states if light.is_hint_state(state)), None)
        if state:
            light.update_state(state)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    light_list = assistant.entries["light"]
    if light_list:
        async_add_entities(light_list)


class DnakeLight(LightEntity):

    def __init__(self, device):
        self._name = device.get("na")
        self._dev_no = device.get("nm")
        self._dev_ch = device.get("ch")
        self._is_on = False

    def is_hint_state(self, state):
        return state.get("devNo") == self._dev_no and state.get("devCh") == self._dev_ch

    @property
    def unique_id(self):
        return f"dnake_{self._dev_ch}_{self._dev_no}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"light_{self._dev_ch}_{self._dev_no}")},
            name=self._name,
            manufacturer=MANUFACTURER,
            model="灯光控制",
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
    def color_mode(self):
        return ColorMode.ONOFF

    @property
    def supported_color_modes(self):
        return {ColorMode.ONOFF}

    async def async_turn_on(self, **kwargs):
        await self._turn_to(True)

    async def async_turn_off(self, **kwargs):
        await self._turn_to(False)

    async def _turn_to(self, is_on):
        is_success = await self.hass.async_add_executor_job(
            assistant.turn_to,
            self._dev_no,
            self._dev_ch,
            is_on,
        )
        if is_success:
            self._is_on = is_on
            self.async_write_ha_state()

    def update_state(self, state):
        self._is_on = state.get("state", 0) == 1
        self.async_write_ha_state()
