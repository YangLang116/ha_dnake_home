import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .core.assistant import assistant
from .cover import load_covers, update_covers_state
from .light import load_lights, update_lights_state
from .climate import load_climates, update_climates_state

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.COVER, Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    gateway_ip = entry.data["gateway_ip"]
    auth_username = entry.data["auth_username"]
    auth_password = entry.data["auth_password"]
    assistant.bind_auth_info(gateway_ip, auth_username, auth_password)
    iot_info = await hass.async_add_executor_job(assistant.query_iot_info)
    if iot_info:
        iot_device_name = iot_info.get("iot_device_name")
        gw_iot_name = iot_info.get("gw_iot_name")
        assistant.bind_iot_info(iot_device_name, gw_iot_name)
        device_list = await hass.async_add_executor_job(assistant.query_device_list)
        if device_list:
            # 设备分类
            load_lights(device_list)
            load_covers(device_list)
            load_climates(device_list)
            # 初始化各类设备
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

            async def _async_refresh_states(now=None):
                _LOGGER.info("update all device state")
                states = await hass.async_add_executor_job(assistant.read_all_dev_state)
                update_lights_state(states)
                update_covers_state(states)
                update_climates_state(states)

            # 初始化设备状态
            await _async_refresh_states()
            # 定时刷新设备状态
            time_delta = timedelta(seconds=entry.data["scan_interval"])
            async_track_time_interval(hass, _async_refresh_states, time_delta)
            return True
        else:
            _LOGGER.error("query_device_list fail")
            return False
    else:
        _LOGGER.error("query_iot_info fail")
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
