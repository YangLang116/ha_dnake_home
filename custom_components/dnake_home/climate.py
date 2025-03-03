import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.components.climate import ClimateEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.climate.const import (
    FAN_LOW,
    FAN_MIDDLE,
    FAN_HIGH,
    ClimateEntityFeature,
    HVACMode,
)

from .core.assistant import assistant
from .core.utils import get_key_by_value

_LOGGER = logging.getLogger(__name__)

_hvac_table = {
    HVACMode.OFF: 0,
    HVACMode.HEAT: 1,
    HVACMode.COOL: 2,
    HVACMode.FAN_ONLY: 3,
    HVACMode.DRY: 4,
}

_fan_table = {FAN_LOW: 0, FAN_MIDDLE: 1, FAN_HIGH: 2}

_min_temperature = 16

_max_temperature = 32


def load_climates(device_list):
    climates = [
        DnakeClimate(device) for device in device_list if device.get("ty") == 16640
    ]
    _LOGGER.info(f"find climate num: {len(climates)}")
    assistant.entries["climate"] = climates


def update_climates_state(states):
    climates = assistant.entries["climate"]
    for climate in climates:
        state = next((state for state in states if climate.is_hint_state(state)), None)
        if state:
            climate.update_state(state)
            climate.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    climate_list = assistant.entries["climate"]
    if climate_list:
        async_add_entities(climate_list)


class DnakeClimate(ClimateEntity):

    def __init__(self, device):
        self._name = device.get("na")
        self._dev_no = device.get("nm")
        self._dev_ch = device.get("ch")
        self._target_temperature = _min_temperature
        self._current_temperature = _min_temperature
        self._hvac_mode = HVACMode.OFF
        self._fan_mode = FAN_LOW

    def is_hint_state(self, state):
        return state.get("devNo") == self._dev_no and state.get("devCh") == self._dev_ch

    @property
    def unique_id(self):
        return f"dnake_{self._dev_ch}_{self._dev_no}"

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def current_temperature(self):
        return self._current_temperature

    @property
    def min_temp(self):
        return _min_temperature

    @property
    def max_temp(self):
        return _max_temperature

    @property
    def target_temperature_step(self):
        return 1

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return list(_hvac_table.keys())

    @property
    def fan_mode(self):
        return self._fan_mode

    @property
    def fan_modes(self):
        return list(_fan_table.keys())

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

    async def _async_turn_to(self, is_open: bool):
        return await self.hass.async_add_executor_job(
            assistant.set_air_condition_power,
            self._dev_no,
            self._dev_ch,
            is_open,
        )

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get("temperature")
        is_success = await self.hass.async_add_executor_job(
            assistant.set_air_condition_temperature,
            self._dev_no,
            self._dev_ch,
            temperature,
        )
        if is_success:
            self._target_temperature = temperature

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            close_success = await self._async_turn_to(False)
            if close_success:
                self._hvac_mode = HVACMode.OFF
                self.async_write_ha_state()
        else:
            if self._hvac_mode == HVACMode.OFF:
                open_success = await self._async_turn_to(True)
                if not open_success:
                    return
            switch_success = await self.hass.async_add_executor_job(
                assistant.set_air_condition_mode,
                self._dev_no,
                self._dev_ch,
                _hvac_table[hvac_mode],
            )
            if switch_success:
                self._hvac_mode = hvac_mode
                self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        is_success = await self.hass.async_add_executor_job(
            assistant.set_air_condition_fan,
            self._dev_no,
            self._dev_ch,
            _fan_table[fan_mode],
        )
        if is_success:
            self._fan_mode = fan_mode
            self.async_write_ha_state()

    def update_state(self, state):
        self._target_temperature = state.get("tempDesire", _min_temperature)
        self._current_temperature = state.get("tempIndoor", _min_temperature)
        self._fan_mode = get_key_by_value(_fan_table, state.get("speed"), FAN_LOW)
        if state.get("powerOn", 0) == 0:
            self._hvac_mode = HVACMode.OFF
        else:
            mode = state.get("mode")
            self._hvac_mode = get_key_by_value(_hvac_table, mode, HVACMode.OFF)
