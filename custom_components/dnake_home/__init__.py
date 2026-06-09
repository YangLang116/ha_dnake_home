import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .climate import load_climates, update_climates_state
from .core.assistant import assistant
from .cover import load_covers, update_covers_state
from .fan import load_fans, update_fans_state
from .light import load_lights, update_lights_state
from .sensor import load_sensors, update_sensors_state

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.COVER, Platform.CLIMATE, Platform.SENSOR, Platform.FAN]

DEVICE_LOADERS = [
    load_lights,
    load_covers,
    load_climates,
    load_sensors,
    load_fans,
]

STATE_UPDATERS = [
    update_lights_state,
    update_covers_state,
    update_climates_state,
    update_sensors_state,
    update_fans_state,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    gateway_ip = entry.data["gateway_ip"]
    auth_username = entry.data["auth_username"]
    auth_password = entry.data["auth_password"]
    assistant.bind_auth_info(gateway_ip, auth_username, auth_password)
    iot_info = await hass.async_add_executor_job(assistant.query_iot_info)
    if not iot_info:
        _LOGGER.error("query_iot_info fail")
        return False

    iot_device_name = iot_info.get("iot_device_name")
    gw_iot_name = iot_info.get("gw_iot_name")
    if not iot_device_name or not gw_iot_name:
        _LOGGER.error("iot info missing required device names: %s", iot_info)
        return False

    assistant.bind_iot_info(iot_device_name, gw_iot_name)
    device_list = await hass.async_add_executor_job(assistant.query_device_list)
    if device_list:
        for loader in DEVICE_LOADERS:
            loader(device_list)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        async def _async_refresh_states(now=None):
            _LOGGER.info("update all device state")
            states = await hass.async_add_executor_job(assistant.read_all_dev_state)
            if not states:
                _LOGGER.warning("skip device state update because read_all_dev_state returned no states")
                return
            for updater in STATE_UPDATERS:
                updater(states)

        await _async_refresh_states()
        time_delta = timedelta(seconds=entry.data["scan_interval"])
        refresh_cancel = async_track_time_interval(hass, _async_refresh_states, time_delta)

        entry.async_on_unload(refresh_cancel)
        return True
    else:
        _LOGGER.error("query_device_list fail")
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_result:
        assistant.entries.clear()
        assistant.gw_ip = None
        assistant.auth = None
        assistant.from_device = None
        assistant.to_device = None
        _LOGGER.info("Dnake Home integration unloaded successfully")

    return unload_result
