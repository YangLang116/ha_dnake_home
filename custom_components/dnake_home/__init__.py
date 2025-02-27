import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .assistant import assistant
from .cover import find_covers, update_covers_state
from .light import find_lights, update_lights_state

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.COVER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    gateway_ip = entry.data['gateway_ip']
    auth_username = entry.data['auth_username']
    auth_password = entry.data['auth_password']
    assistant.bind_auth_info(gateway_ip, auth_username, auth_password)
    iot_info = await hass.async_add_executor_job(assistant.query_iot_info)
    if iot_info:
        iot_device_name = iot_info.get('iot_device_name')
        gw_iot_name = iot_info.get('gw_iot_name')
        assistant.bind_iot_info(iot_device_name, gw_iot_name)
        device_list = await hass.async_add_executor_job(assistant.query_device_list)
        if not device_list:
            _LOGGER.error('async_setup_entry query_device_list fail')
            return False
        # 设备分类
        light_list = find_lights(device_list)
        cover_list = find_covers(device_list)
        entry.data['light_list'] = light_list
        entry.data['cover_list'] = cover_list

        # 刷新设备状态
        async def async_update_devices(now=None):
            """更新所有设备状态."""
            _LOGGER.debug("Updating Dnake cover states")
            device_states = await hass.async_add_executor_job(assistant.read_all_dev_state)
            update_lights_state(light_list, device_states)
            update_covers_state(cover_list, device_states)

        await async_update_devices()
        scan_interval = entry.data.get("scan_interval", 30)
        async_track_time_interval(hass, async_update_devices, timedelta(seconds=scan_interval))

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    else:
        _LOGGER.error('async_setup_entry query_iot_info fail')
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # 卸载平台
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok
