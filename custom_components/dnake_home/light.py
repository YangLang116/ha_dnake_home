import logging

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import assistant

_LOGGER = logging.getLogger(__name__)


def find_lights(device_list):
    result = []
    for device in device_list:
        if device.get('ty') == 256:
            result.append(DnakeLight(device))
    return result


def update_lights_state(light_list, state_list):
    for light in light_list:
        for device_state in state_list:
            if light._dev_no == device_state.get("devNo") and light._dev_ch == device_state.get("devCh"):
                light.set_state(device_state)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Dnake lights from a config entry."""
    light_list = entry.data['light_list']
    if light_list:
        async_add_entities(light_list)


class DnakeLight(LightEntity):
    """Representation of a Dnake Light."""

    def __init__(self, device):
        """Initialize the light."""
        self._device = device
        self._name = device.get("na")
        self._is_on = device.get("state") == 1
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF
        self._dev_no = device.get("nm")
        self._dev_ch = device.get("ch")

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for this light."""
        return f"dnake_{self._dev_ch}_{self._dev_no}"

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._is_on

    @property
    def supported_color_modes(self):
        """Return supported color modes."""
        return self._attr_supported_color_modes

    @property
    def color_mode(self):
        """Return the current color mode."""
        return self._attr_color_mode

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        is_success = assistant.switch(self._dev_no, self._dev_ch, True)
        if is_success:
            self._is_on = True
            self.async_write_ha_state()

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        is_success = assistant.switch(self._dev_no, self._dev_ch, False)
        if is_success:
            self._is_on = False
            self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for this light."""
        state = assistant.read_dev_state(self._dev_no, self._dev_ch)
        if state and state['result'] == 'ok':
            self.set_state(state)

    def set_state(self, device_state):
        self._is_on = device_state.get("state") == 1
        self.async_write_ha_state()
